import logging
import asyncio
from app.engine.scraper import WebScraper
from app.engine.gemini_provider import GeminiProvider
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SentimentEngine:
    """performs layer 2 analysis: reputation search + ai analysis."""
    
    def __init__(self):
        self.scraper = WebScraper()
        self.ai = GeminiProvider()

    async def analyze(self, company_name: str, layer1_data: Dict[str, Any]) -> Dict[str, Any]:
        """runs reputation search and ai analysis on company."""
        logger.info(f"starting layer 2: {company_name}")
        
        try:
            rep_data = await asyncio.to_thread(self.scraper.perform_reputation_search, company_name)
        except Exception as e:
            logger.error(f"rep search err: {e}")
            rep_data = []

        ai_result = await asyncio.to_thread(self.ai.analyze_company, company_name, layer1_data, rep_data)
        
        return {
            "reputation_search": rep_data,
            "ai_analysis": ai_result
        }
