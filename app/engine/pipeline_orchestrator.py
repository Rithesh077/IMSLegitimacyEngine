from app.engine.lookup_engine import LookupEngine
from app.engine.scraper import WebScraper
from app.engine.sentiment_engine import SentimentEngine
from app.schemas.company import CompanyInput, CredibilityAnalysis
import logging
import asyncio

logger = logging.getLogger(__name__)

class PipelineOrchestrator:
    """
    Orchestrates the company verification pipeline.
    Aggregates signals from Registry lookups, LinkedIn verification, and Website analysis.
    """
    
    def __init__(self):
        self.lookup_engine = LookupEngine() 
        self.scraper = WebScraper()
        self.sentiment = SentimentEngine()

    async def run_pipeline(self, input_data: CompanyInput) -> CredibilityAnalysis:
        logger.info(f"pipeline start: {input_data.name}")
        
        signals = {
            "registry_link_found": False,
            "registry_breakdown": {},
            "linkedin_verified": False,
            "website_content_match": False,
            "email_domain_match": False,
            "hr_verified": False,
            "address_verified": False
        }
        
        match_details = {
            "input_vs_search_score": 0,
            "input_vs_pdl_score": 0,
            "matches": []
        }
        
        pdl_data = {}
        all_search_results = []


        
        # registry lookup (if id provided)
        if input_data.registry_id:
            logger.info("fetching registry data...")
            web = input_data.website_urls[0] if input_data.website_urls else None
            
            breakdown, _ = await self.lookup_engine.check_registry_and_metadata(
                input_data.name, input_data.country, input_data.registry_id,
                input_data.linkedin_url, web
            )
            signals["registry_breakdown"] = breakdown
            
            # check matches in registry results
            best_score = 0
            for domain, data in breakdown.items():
                if domain == "peopledatalabs.com": continue
                res = data.get("search_results", [])
                all_search_results.extend(res)
                for r in res:
                    sc = self.scraper.calculate_fuzzy_match(input_data.name, r.get('title', ''))
                    best_score = max(best_score, sc)
                        
            match_details["input_vs_search_score"] = best_score
            if best_score > 70:
                match_details["matches"].append("registry match")
            
            signals["registry_link_found"] = any(v.get("found") for k,v in breakdown.items() if k != "peopledatalabs.com")

        # digital footprint
        if input_data.linkedin_url:
            signals["linkedin_verified"] = self.scraper.verify_url_owner(
                input_data.linkedin_url, input_data.name
            )
            
        if input_data.website_urls:
             for url in input_data.website_urls:
                 if self.scraper.verify_url_owner(url, input_data.name):
                     signals["website_content_match"] = True
                     break
        
        # email domain verification
        if input_data.hr_email and "@" in input_data.hr_email:
            email_domain = input_data.hr_email.split("@")[-1].lower()
            
            # Extract website domain
            web_domain = ""
            if input_data.website_urls:
                 try:
                     from urllib.parse import urlparse
                     parsed = urlparse(input_data.website_urls[0])
                     web_domain = parsed.netloc.replace("www.", "").lower()
                 except: pass

            if web_domain and (email_domain == web_domain or web_domain.endswith(f".{email_domain}") or email_domain.endswith(f".{web_domain}")):
                signals["email_domain_match"] = True
                match_details["matches"].append("email domain match")
            else:
                # Check for academic domain mismatch
                logger.warning(f"Email domain mismatch: {email_domain} vs {web_domain}")
                if "edu" in email_domain:
                    match_details["matches"].append("university email detected (warning)")

        # parallel verification (hr & address)
        logger.info("verifying hr and address associations...")
        hr_task = asyncio.to_thread(self.scraper.verify_association, input_data.name, input_data.hr_name)
        
        # Only verify address if provided
        if input_data.registered_address:
            addr_task = asyncio.to_thread(self.scraper.verify_association, input_data.name, input_data.registered_address)
            hr_check, addr_check = await asyncio.gather(hr_task, addr_task)
        else:
            # Run only HR task
            hr_check = await hr_task
            addr_check = {"verified": False, "score": 0}

        if hr_check["verified"]:
            signals["hr_verified"] = True
            match_details["matches"].append("hr verified")
        
        if addr_check.get("verified"):
            signals["address_verified"] = True
            match_details["matches"].append("address verified")

        # holistic scoring
        score = 0
        
        # registry (40 pts)
        if signals["registry_link_found"]: 
            score += 40
        
        # digital footprint (20 pts)
        if signals["linkedin_verified"]: score += 10
        if signals["website_content_match"]: score += 10
        if signals["email_domain_match"]: score += 10
        
        # verification signals (40 pts)
        if signals["hr_verified"]: score += 25
        if signals["address_verified"]: score += 15
            
        status = "Verified" if score >= 60 else "Pending"

        # layer 2 (ai analysis)
        l2_context = {
            "signals": signals, 
            "pdl_data": pdl_data,
            "industry": input_data.industry,
            "hr_data": {"name": input_data.hr_name, "email": input_data.hr_email},
            "address_data": {"input": input_data.registered_address, "verified": signals["address_verified"]}
        }
        ai_res = await self.sentiment.analyze(input_data.name, l2_context)
        ai_data = ai_res.get("ai_analysis", {})
        
        # override rule-based score with ai score
        final_score = float(ai_data.get("trust_score", score))
        final_tier = ai_data.get("classification", "Pending")
        
        # construct final analysis object
        analysis_obj = CredibilityAnalysis(
             trust_score=final_score,
             trust_tier=final_tier,
             verification_status="Verified" if final_score >= 60 else "Pending",
             review_count=0,
             sentiment_summary=ai_data.get("analysis", "pending analysis"),
             scraped_sources=[],
             red_flags=ai_data.get("flags", []),
             details={
                 "signals": signals,
                 "match_details": match_details,
                 "pdl_data": pdl_data,
                 "inputs_provided": {
                     "registry_id": bool(input_data.registry_id),
                     "hr_name": bool(input_data.hr_name),
                     "address": bool(input_data.registered_address)
                 }
             }
         )
        
        # generate reporting artifacts
        try:
            # pdf report
            from app.core.report_generator import ReportGenerator
            report_gen = ReportGenerator(analysis_obj, input_data.name)
            pdf_path = report_gen.generate()
            analysis_obj.details["report_path"] = pdf_path
            
            # master excel log
            from app.core.excel_logger import ExcelLogger
            ExcelLogger.log_verification(input_data, analysis_obj)
            
        except Exception as e:
            logger.error(f"Reporting failed: {e}")
            analysis_obj.details["reporting_error"] = str(e)
            
        return analysis_obj
