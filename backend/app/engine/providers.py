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

    def check_registry_signal(self, registration_id: str, company_name: str) -> Dict[str, Any]:
        """
        verifies company presence across trusted domains using dual-query strategy.
        returns: { domain: { found: bool, matches: list } }
        """
        results = {}
        clean_id = registration_id.lower().strip()
        logger.info(f"checking registry: {registration_id}")
        
        for domain in self.TRUSTED_DOMAINS:
            res = {
                "found": False,
                "verification_method": None,
                "search_results": []
            }
            
            # 1. strict query (name + id)
            q1 = f'{domain} {company_name} {registration_id}'
            found1, data1 = self._check_query(q1, domain, company_name, clean_id, strict_id=True)
            res["search_results"].extend(data1)
            
            if found1:
                res["found"] = True
                res["verification_method"] = "strict_id"

            # 2. broad query (name only)
            # running broad search to capture all context even if strict failed
            q2 = f'{domain} {company_name}'
            found2, data2 = self._check_query(q2, domain, company_name, clean_id, strict_id=False)
            res["search_results"].extend(data2)
            
            if not res["found"] and found2:
                res["found"] = True
                res["verification_method"] = "name_match"
            
            results[domain] = res
            
        return results

    def _check_query(self, query: str, domain: str, expected_name: str, expected_id: str, strict_id: bool) -> tuple[bool, List[Dict]]:
        """
        Parses search results to confirm a match.
        Returns: (is_match, list_of_results)
        """
        results = self.scraper.search_web(query, num_results=5) # Increased to 5 per user req
        is_match = False
        
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
                        is_match = True
                else:
                    # Stricter Name Match required if ID is absent
                    if name_score > 70:
                        logger.info(f"  -> Match Confirmed: Name Score: {name_score}")
                        is_match = True
                        
        return is_match, results
        
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
