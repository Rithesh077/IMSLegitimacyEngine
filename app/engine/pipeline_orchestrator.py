from app.engine.lookup_engine import LookupEngine
from app.engine.scraper import WebScraper
from app.engine.sentiment_engine import SentimentEngine
from app.schemas.company import CompanyInput, CredibilityAnalysis
from app.models.company import Company
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from urllib.parse import urlparse
import logging
import asyncio
import uuid

logger = logging.getLogger(__name__)

class PipelineOrchestrator:
    """verification pipeline: registry + signals"""

    def __init__(self):
        self.lookup_engine = LookupEngine()
        self.scraper = WebScraper()
        self.sentiment = SentimentEngine()

    async def run_pipeline(self, input_data: CompanyInput, db: AsyncSession = None) -> CredibilityAnalysis:
        logger.info(f"pipeline: {input_data.name}")

        signals = {
            "registry_link_found": False, "registry_breakdown": {},
            "linkedin_verified": False, "website_content_match": False,
            "email_domain_match": False, "hr_verified": False, "address_verified": False
        }
        match_details = {"input_vs_search_score": 0, "input_vs_pdl_score": 0, "matches": []}
        pdl_data = {}

        # parallel verification tasks
        async def do_registry():
            if not input_data.registry_id: return {}, 0
            web = input_data.website_urls[0] if input_data.website_urls else None
            breakdown, _ = await self.lookup_engine.check_registry_and_metadata(
                input_data.name, input_data.country, input_data.registry_id, input_data.linkedin_url, web
            )
            best = 0
            for domain, data in breakdown.items():
                if domain == "peopledatalabs.com": continue
                for r in data.get("search_results", []):
                    best = max(best, self.scraper.calculate_fuzzy_match(input_data.name, r.get('title', '')))
            return breakdown, best

        async def do_linkedin():
            if not input_data.linkedin_url: return False
            return await asyncio.to_thread(self.scraper.verify_url_owner, input_data.linkedin_url, input_data.name)

        async def do_website():
            if not input_data.website_urls: return False
            return await asyncio.to_thread(self.scraper.verify_url_owner, input_data.website_urls[0], input_data.name)

        async def do_hr():
            if not input_data.hr_name: return {"verified": False, "score": 0}
            return await asyncio.to_thread(self.scraper.verify_association, input_data.name, input_data.hr_name)

        async def do_address():
            if not input_data.registered_address: return {"verified": False, "score": 0}
            return await asyncio.to_thread(self.scraper.verify_association, input_data.name, input_data.registered_address)

        # run all checks in parallel
        reg, linkedin, website, hr, addr = await asyncio.gather(
            do_registry(), do_linkedin(), do_website(), do_hr(), do_address()
        )

        # process results
        breakdown, best_score = reg
        signals["registry_breakdown"] = breakdown
        match_details["input_vs_search_score"] = best_score
        if best_score > 70: match_details["matches"].append("registry match")
        signals["registry_link_found"] = any(v.get("found") for k,v in breakdown.items() if k != "peopledatalabs.com")
        signals["linkedin_verified"] = linkedin
        signals["website_content_match"] = website
        if hr.get("verified"):
            signals["hr_verified"] = True
            match_details["matches"].append("hr verified")
        if addr.get("verified"):
            signals["address_verified"] = True
            match_details["matches"].append("address verified")

        # email domain check
        if input_data.hr_email and "@" in input_data.hr_email:
            email_domain = input_data.hr_email.split("@")[-1].lower()
            web_domain = ""
            if input_data.website_urls:
                try:
                    web_domain = urlparse(input_data.website_urls[0]).netloc.replace("www.", "").lower()
                except: pass
            if web_domain and (email_domain == web_domain or web_domain.endswith(f".{email_domain}") or email_domain.endswith(f".{web_domain}")):
                signals["email_domain_match"] = True
                match_details["matches"].append("email domain match")

        # scoring
        score = 0
        if signals["registry_link_found"]: score += 40
        if signals["linkedin_verified"]: score += 10
        if signals["website_content_match"]: score += 10
        if signals["email_domain_match"]: score += 10
        if signals["hr_verified"]: score += 25
        if signals["address_verified"]: score += 15

        # ai analysis (always run)
        l2_context = {
            "signals": signals, "pdl_data": pdl_data, "industry": input_data.industry,
            "hr_data": {"name": input_data.hr_name, "email": input_data.hr_email},
            "address_data": {"input": input_data.registered_address, "verified": signals["address_verified"]}
        }
        ai_res = await self.sentiment.analyze(input_data.name, l2_context)
        ai_data = ai_res.get("ai_analysis", {})
        final_score = float(ai_data.get("trust_score", score))
        final_tier = ai_data.get("classification", "Pending")

        analysis_obj = CredibilityAnalysis(
            trust_score=final_score, trust_tier=final_tier,
            verification_status="Verified" if final_score >= 60 else "Pending",
            review_count=0, sentiment_summary=ai_data.get("analysis", "signal-based"),
            scraped_sources=[], red_flags=ai_data.get("flags", []),
            details={
                "signals": signals, "match_details": match_details, "pdl_data": pdl_data,
                "inputs_provided": {
                    "registry_id": bool(input_data.registry_id), "hr_name": bool(input_data.hr_name),
                    "address": bool(input_data.registered_address), "user_id": bool(input_data.user_id)
                }
            }
        )

        # reporting
        try:
            from app.core.report_generator import ReportGenerator
            report_gen = ReportGenerator(analysis_obj, input_data.name)
            pdf_path = report_gen.generate()
            analysis_obj.details["report_path"] = pdf_path
            if db: await self.save_result(db, input_data, analysis_obj, pdf_path)
            from app.core.excel_logger import ExcelLogger
            ExcelLogger.log_verification(input_data, analysis_obj)
        except Exception as e:
            logger.error(f"report: {e}")
            analysis_obj.details["reporting_error"] = str(e)

        return analysis_obj

    async def save_result(self, db: AsyncSession, input_data: CompanyInput, analysis: CredibilityAnalysis, report_path: str = None):
        """save verification to db"""
        if not input_data.user_id:
            logger.warning("skip db: no user_id")
            return
        try:
            stmt = select(Company).where(Company.company_name.ilike(input_data.name))
            result = await db.execute(stmt)
            existing = result.scalars().first()

            if existing:
                logger.info(f"update: {existing.company_name}")
                existing.verification_status = analysis.verification_status
                existing.ai_trust_score = analysis.trust_score
                existing.ai_trust_tier = analysis.trust_tier
                existing.rejection_reason = ", ".join(analysis.red_flags) if analysis.red_flags else None
                existing.ai_report_path = report_path
                existing.is_approved = analysis.trust_score >= 70
                if not existing.cin and input_data.registry_id: existing.cin = input_data.registry_id
                if not existing.website_url and input_data.website_urls: existing.website_url = input_data.website_urls[0]
            else:
                logger.info(f"create: {input_data.name}")
                company = Company(
                    id=str(uuid.uuid4()), company_name=input_data.name, user_id=input_data.user_id,
                    verification_status=analysis.verification_status, ai_trust_score=analysis.trust_score,
                    ai_trust_tier=analysis.trust_tier,
                    rejection_reason=", ".join(analysis.red_flags) if analysis.red_flags else None,
                    ai_report_path=report_path, is_approved=analysis.trust_score >= 70,
                    hr_name=input_data.hr_name, email=input_data.hr_email,
                    website_url=input_data.website_urls[0] if input_data.website_urls else None,
                    linkedin_url=input_data.linkedin_url, cin=input_data.registry_id,
                    registered_address=input_data.registered_address, country=input_data.country,
                )
                db.add(company)

            await db.commit()
            await db.refresh(existing if existing else company)
            logger.info(f"saved: {existing.id if existing else company.id}")
        except Exception as e:
            logger.error(f"db: {e}")
            await db.rollback()
