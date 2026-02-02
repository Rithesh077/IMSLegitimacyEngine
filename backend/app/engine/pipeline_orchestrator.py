from app.engine.lookup_engine import LookupEngine
from app.engine.scraper import WebScraper
from app.schemas.company import CompanyInput, CredibilityAnalysis
import logging

logger = logging.getLogger(__name__)

class PipelineOrchestrator:
    """
    Orchestrates the company verification pipeline.
    Aggregates signals from Registry lookups, LinkedIn verification, and Website analysis.
    """
    
    def __init__(self):
        self.lookup_engine = LookupEngine() 
        self.scraper = WebScraper()

    async def run_pipeline(self, input_data: CompanyInput) -> CredibilityAnalysis:
        logger.info(f"pipeline start: {input_data.name}")
        
        signals = {
            "registry_link_found": False,
            "registry_breakdown": {},
            "linkedin_verified": False,
            "website_content_match": False
        }
        
        match_details = {
            "input_vs_search_score": 0,
            "input_vs_pdl_score": 0,
            "matches": []
        }
        
        pdl_data = {}
        all_search_results = []

        # 1. registry
        if input_data.registry_id:
            logger.info("fetching registry data...")
            web = input_data.website_urls[0] if input_data.website_urls else None
            
            breakdown, _ = await self.lookup_engine.check_registry_and_metadata(
                input_data.name, input_data.country, input_data.registry_id,
                input_data.linkedin_url, web
            )
            signals["registry_breakdown"] = breakdown
            
            # A. input vs search
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
                match_details["matches"].append("high registry match")

            # B. input vs pdl
            pdl = breakdown.get("peopledatalabs.com", {})
            if pdl.get("found") and (res := pdl.get("search_results")):
                pdl_data = res[0]
                pdl_score = self.scraper.calculate_fuzzy_match(input_data.name, pdl_data.get("name", ""))
                match_details["input_vs_pdl_score"] = pdl_score
                    
            signals["registry_link_found"] = any(v.get("found") for k,v in breakdown.items() if k != "peopledatalabs.com")

        # 2. linkedin
        if input_data.linkedin_url:
            signals["linkedin_verified"] = self.scraper.verify_url_owner(
                input_data.linkedin_url, input_data.name
            )
            
        # 3. website
        if input_data.website_urls:
             for url in input_data.website_urls:
                 if self.scraper.verify_url_owner(url, input_data.name):
                     signals["website_content_match"] = True
                     break
        
        # --- scoring ---
        score = 0
        if match_details["input_vs_pdl_score"] >= 60:
            score += 60
            match_details["matches"].append("strong pdl match")
            
        if signals["registry_link_found"]: 
            score += 40
            
        status = "Verified" if score >= 60 else "Pending"

        return CredibilityAnalysis(
             trust_score=float(score),
             trust_tier="High" if score >= 80 else ("Medium" if score >= 50 else "Low"),
             verification_status=status,
             review_count=0,
             sentiment_summary="signal analysis complete",
             scraped_sources=[],
             red_flags=[],
             details={
                 "signals": signals,
                 "match_details": match_details,
                 "pdl_data": pdl_data,
                 "all_search_results": all_search_results,
                 "inputs_provided": {
                     "registry_id": bool(input_data.registry_id),
                     "linkedin": bool(input_data.linkedin_url),
                     "website": bool(input_data.website_urls)
                 }
             }
         )
