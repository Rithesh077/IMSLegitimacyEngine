from typing import Optional, Dict, Any, List
import logging
from app.engine.registry_provider import RegistryProvider
from app.engine.scraper import WebScraper

logger = logging.getLogger(__name__)

class SearchBasedProvider(RegistryProvider):
    """
    Base provider implementing search-based verification.
    Uses search engine text snippets to verify company existence without direct scraping.
    """
    
    TRUSTED_DOMAINS = [] # Override in subclass

    def __init__(self):
        self.scraper = WebScraper()

    def verify_by_id(self, registration_id: str, company_name: str) -> Optional[Dict[str, Any]]:
        return None

    def check_registry_signal(self, registration_id: str, company_name: str) -> Dict[str, bool]:
        """
        Verifies the company's presence across trusted registry domains.
        
        Strategy:
        1. Attempt strict match: "{domain} {name} {id}" -> Requires ID match + Fuzzy Name > 60.
        2. Fallback check: "{domain} {name}" -> Requires Fuzzy Name > 70.
        """
        results = {}
        clean_id = registration_id.lower().strip()
        logger.info(f"Checking registry signals for ID: {registration_id}")
        
        for domain in self.TRUSTED_DOMAINS:
            found = False
            
            # 1. Primary Check: Name + ID
            query_1 = f'{domain} {company_name} {registration_id}'
            logger.info(f"Checking {domain} (Primary)...")
            
            try:
                if self._check_query(query_1, domain, company_name, clean_id, strict_id=True):
                    found = True
            except Exception as e:
                logger.error(f"Primary check failed for {domain}: {e}")

            # 2. Fallback Check: Name only
            if not found:
                query_2 = f'{domain} {company_name}'
                logger.info(f"Checking {domain} (Fallback)...")
                try:
                    if self._check_query(query_2, domain, company_name, clean_id, strict_id=False):
                        found = True
                except Exception as e:
                    logger.error(f"Fallback check failed for {domain}: {e}")
            
            results[domain] = found
            logger.info(f"Result for {domain}: {'FOUND' if found else 'NOT FOUND'}")
            
        return results

    def _check_query(self, query: str, domain: str, expected_name: str, expected_id: str, strict_id: bool) -> bool:
        """
        Parses search results to confirm a match.
        strict_id: If True, mandates ID presence in the snippet.
        """
        results = self.scraper.search_web(query, num_results=2)
        
        for res in results:
            url = res.get('link', '')
            title = res.get('title', '').lower()
            snippet = res.get('snippet', '').lower()
            
            if domain in url:
                name_score = self.scraper.calculate_fuzzy_match(expected_name, res.get('title', ''))
                
                if strict_id:
                    # Enforce ID presence + Moderate Name Match
                    id_match = expected_id in title or expected_id in snippet
                    if id_match and name_score > 60:
                        logger.info(f"  -> Match Confirmed: ID present, Name Score: {name_score}")
                        return True
                else:
                    # Stricter Name Match required if ID is absent
                    if name_score > 70:
                        logger.info(f"  -> Match Confirmed: Name Score: {name_score}")
                        return True
                        
        return False
        
    def verify_by_name(self, name: str) -> List[Dict[str, Any]]:
        return []

class ZaubaProvider(SearchBasedProvider):
    """Trusted sources for Indian entities."""
    TRUSTED_DOMAINS = [
        "zaubacorp.com", 
        "tofler.in", 
        "mca.gov.in", 
        "thecompanycheck.com", 
        "economictimes.indiatimes.com",
        "instafinancials.com"
    ]

    def verify_by_id(self, registration_id: str, company_name: str = "") -> Optional[Dict[str, Any]]:
        return super().verify_by_id(registration_id, company_name)


class OpenCorporatesProvider(SearchBasedProvider):
    """Trusted global sources."""
    TRUSTED_DOMAINS = [
        "opencorporates.com",
        "dnb.com", 
        "sec.gov" 
    ]
    
    def verify_by_id(self, registration_id: str, company_name: str = "") -> Optional[Dict[str, Any]]:
        return super().verify_by_id(registration_id, company_name)
