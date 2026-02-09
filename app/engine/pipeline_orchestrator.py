from app.engine.lookup_engine import LookupEngine
from app.engine.scraper import WebScraper
from app.engine.sentiment_engine import SentimentEngine
from app.schemas.company import CompanyInput, CredibilityAnalysis
from app.models.company import Company
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from urllib.parse import urlparse
from fastapi import BackgroundTasks
import logging
import asyncio
import uuid

logger = logging.getLogger(__name__)

class PipelineOrchestrator:
    """verification: mandatory parallel + optional background"""

    def __init__(self):
        self.lookup_engine = LookupEngine()
        self.scraper = WebScraper()
        self.sentiment = SentimentEngine()

    async def run_fast_pipeline(self, input_data: CompanyInput, db: AsyncSession, background_tasks: BackgroundTasks) -> CredibilityAnalysis:
        """mandatory checks + ai parallel, optional in background via FastAPI BackgroundTasks"""
        logger.info(f"fast pipeline: {input_data.name}")

        # mandatory parallel checks
        async def do_registry():
            if not input_data.registry_id: return {}, False
            breakdown, _ = await self.lookup_engine.check_registry_and_metadata(
                input_data.name, input_data.country, input_data.registry_id,
                input_data.linkedin_url,
                input_data.website_urls[0] if input_data.website_urls else None
            )
            found = any(v.get("found") for k,v in breakdown.items() if k != "peopledatalabs.com")
            return breakdown, found

        async def do_hr():
            if not input_data.hr_name: return {"verified": False, "score": 0}
            return await asyncio.to_thread(self.scraper.verify_association, input_data.name, input_data.hr_name)

        # run mandatory checks in parallel
        registry_result, hr_result = await asyncio.gather(do_registry(), do_hr())
        
        registry_breakdown, registry_found = registry_result
        hr_verified = hr_result.get("verified", False)

        # email domain check (no network)
        email_match = False
        if input_data.hr_email and "@" in input_data.hr_email and input_data.website_urls:
            try:
                email_domain = input_data.hr_email.split("@")[-1].lower()
                web_domain = urlparse(input_data.website_urls[0]).netloc.replace("www.", "").lower()
                email_match = email_domain == web_domain or web_domain.endswith(f".{email_domain}")
            except: pass

        # ai analysis with mandatory data
        ai_context = {
            "signals": {"registry_link_found": registry_found, "email_domain_match": email_match, "hr_verified": hr_verified},
            "pdl_data": registry_breakdown.get("peopledatalabs.com", {}).get("search_results", []),
            "industry": input_data.industry,
            "hr_data": {"name": input_data.hr_name, "email": input_data.hr_email, "verified": hr_verified},
            "address_data": {"input": input_data.registered_address}
        }
        ai_res = await self.sentiment.analyze(input_data.name, ai_context)
        ai_data = ai_res.get("ai_analysis", {})

        # score from mandatory checks
        mandatory_score = 0
        if registry_found: mandatory_score += 40
        if email_match: mandatory_score += 10
        if hr_verified: mandatory_score += 15
        
        ai_score = float(ai_data.get("trust_score", mandatory_score))
        tier = ai_data.get("classification", "Needs Review" if mandatory_score < 40 else "Verified")
        summary = ai_data.get("analysis", f"registry {'found' if registry_found else 'not found'}, hr {'verified' if hr_verified else 'pending'}")

        # generate pdf
        report_path = None
        try:
            from app.core.report_generator import ReportGenerator
            full_analysis = CredibilityAnalysis(
                trust_score=ai_score, trust_tier=tier,
                verification_status="Verified" if ai_score >= 60 else "Pending",
                review_count=0, sentiment_summary=summary, scraped_sources=[],
                red_flags=ai_data.get("flags", []),
                details={"signals": {"registry_link_found": registry_found, "email_domain_match": email_match, "hr_verified": hr_verified}}
            )
            report_gen = ReportGenerator(full_analysis, input_data.name)
            report_path = report_gen.generate()

            from app.core.excel_logger import ExcelLogger
            ExcelLogger.log_verification(input_data, full_analysis)
        except Exception as e:
            logger.error(f"report: {e}")

        # add background task to FastAPI queue
        background_tasks.add_task(
            self._run_optional_and_save, 
            input_data, ai_score, registry_found, email_match, hr_verified, report_path
        )

        # return full object (pending background checks)
        return CredibilityAnalysis(
            trust_score=ai_score,
            trust_tier=tier,
            verification_status="Verified" if ai_score >= 60 else "Pending",
            review_count=0,
            sentiment_summary=summary,
            scraped_sources=[],
            red_flags=ai_data.get("flags", []),
            details={
                "signals": {
                    "registry_link_found": registry_found, 
                    "email_domain_match": email_match, 
                    "hr_verified": hr_verified,
                    "linkedin_verified": False,
                    "website_verified": False, 
                    "address_verified": False
                },
                "registry_breakdown": registry_breakdown,
                "report_path": report_path,
                "note": "Initial score. Background checks in progress."
            }
        )

    async def _run_optional_and_save(self, input_data: CompanyInput, base_score: float, 
                                      registry_found: bool, email_match: bool, hr_verified: bool,
                                      report_path: str):
        """background: optional checks (linkedin, website, address), then save to db"""
        logger.info(f"background started: {input_data.name}")
        
        linkedin_verified = False
        website_verified = False
        address_verified = False
        
        try:
            async def do_linkedin():
                if not input_data.linkedin_url: return False
                return await asyncio.to_thread(self.scraper.verify_url_owner, input_data.linkedin_url, input_data.name)

            async def do_website():
                if not input_data.website_urls: return False
                return await asyncio.to_thread(self.scraper.verify_url_owner, input_data.website_urls[0], input_data.name)

            async def do_address():
                if not input_data.registered_address: return {"verified": False}
                return await asyncio.to_thread(self.scraper.verify_association, input_data.name, input_data.registered_address)

            linkedin, website, addr = await asyncio.gather(do_linkedin(), do_website(), do_address())
            
            linkedin_verified = linkedin
            website_verified = website
            address_verified = addr.get("verified", False)

        except Exception as e:
            logger.error(f"optional checks: {e}")

        # calculate final score
        final_score = base_score
        if linkedin_verified: final_score += 10
        if website_verified: final_score += 10
        if address_verified: final_score += 10
        
        final_tier = "Verified" if final_score >= 60 else "Needs Review"
        logger.info(f"final score: {input_data.name} = {final_score}")

        # save to db
        if input_data.user_id:
            await self._save_to_db(input_data, final_score, final_tier, report_path)

    async def _save_to_db(self, input_data: CompanyInput, score: float, tier: str, report_path: str):
        """save verification to db"""
        try:
            from app.core.database import async_session
            async with async_session() as db:
                stmt = select(Company).where(Company.company_name.ilike(input_data.name))
                result = await db.execute(stmt)
                existing = result.scalars().first()

                if existing:
                    existing.verification_status = "Verified" if score >= 60 else "Pending"
                    existing.ai_trust_score = score
                    existing.ai_trust_tier = tier
                    existing.ai_report_path = report_path
                    existing.is_approved = score >= 70
                else:
                    company = Company(
                        id=str(uuid.uuid4()), company_name=input_data.name, user_id=input_data.user_id,
                        verification_status="Verified" if score >= 60 else "Pending",
                        ai_trust_score=score, ai_trust_tier=tier, ai_report_path=report_path,
                        is_approved=score >= 70, hr_name=input_data.hr_name, email=input_data.hr_email,
                        website_url=input_data.website_urls[0] if input_data.website_urls else None,
                        linkedin_url=input_data.linkedin_url, cin=input_data.registry_id,
                        registered_address=input_data.registered_address, country=input_data.country,
                    )
                    db.add(company)

                await db.commit()
                logger.info(f"db saved: {input_data.name}")
        except Exception as e:
            logger.error(f"db: {e}")

    async def run_pipeline(self, input_data: CompanyInput, db: AsyncSession, background_tasks: BackgroundTasks) -> CredibilityAnalysis:
        """legacy wrapper"""
        return await self.run_fast_pipeline(input_data, db, background_tasks)
