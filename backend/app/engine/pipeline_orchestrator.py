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
        logger.info(f"Initiating pipeline for: {input_data.name}")
        
        signals = {
            "registry_link_found": False,
            "registry_breakdown": {},
            "linkedin_verified": False,
            "website_content_match": False
        }
        
        # 1. Registry Signal Breakdown
        # Checks for presence across multiple trusted domains (Zauba, Tofler, etc.)
        if input_data.registry_id:
            logger.info("Verifying registry presence...")
            # Await the async caching call
            breakdown = await self.lookup_engine.check_registry_presence(
                input_data.name, input_data.country, input_data.registry_id
            )
            signals["registry_breakdown"] = breakdown
            
            # Count successful hits
            hits = sum(1 for v in breakdown.values() if v)
            if hits > 0:
                signals["registry_link_found"] = True
                
            logger.info(f"Registry Confirmation Hits: {hits}/{len(breakdown)}")
        
        # 2. LinkedIn Verification (Reverse Search)
        if input_data.linkedin_url:
            logger.info("Verifying LinkedIn URL ownership...")
            signals["linkedin_verified"] = self.scraper.verify_url_owner(
                input_data.linkedin_url, input_data.name
            )
            
        # 3. Website Verification (Reverse Search)
        if input_data.website_urls:
             logger.info("Verifying Website ownership...")
             for url in input_data.website_urls:
                 if self.scraper.verify_url_owner(url, input_data.name):
                     signals["website_content_match"] = True
                     break
        
        # Scoring Logic
        # Registry hits are weighted heavily (40pts), with bonus for multiple sources.
        score = 0
        if signals["registry_link_found"]: 
            score += 40
            
            hits = sum(1 for v in signals["registry_breakdown"].values() if v)
            if hits > 1: score += 10 # Bonus for corroboration
            
        if signals["linkedin_verified"]: score += 25
        if signals["website_content_match"]: score += 25
        
        # Status Determination
        # Simplified: Either Verified or Unverified. No "Rejected".
        status = "Verified" if score >= 60 else "Unverified"

        return CredibilityAnalysis(
             trust_score=float(score),
             trust_tier="High" if score >= 80 else ("Medium" if score >= 50 else "Low"),
             verification_status=status,
             review_count=0,
             sentiment_summary="Signal Analysis Complete",
             scraped_sources=[],
             red_flags=[],
             details={
                 "signals": signals,
                 "inputs_provided": {
                     "registry_id": bool(input_data.registry_id),
                     "linkedin": bool(input_data.linkedin_url),
                     "website": bool(input_data.website_urls)
                 }
             }
         )
