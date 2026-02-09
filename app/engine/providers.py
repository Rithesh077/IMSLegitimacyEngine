from typing import Optional, Dict, Any, List
import logging
from concurrent.futures import ThreadPoolExecutor
from app.engine.registry_provider import RegistryProvider
from app.engine.scraper import WebScraper

logger = logging.getLogger(__name__)

class SearchBasedProvider(RegistryProvider):
    """search-based registry verification"""
    TRUSTED_DOMAINS = []

    def __init__(self):
        self.scraper = WebScraper()

    def verify_by_id(self, registration_id: str, company_name: str) -> Optional[Dict[str, Any]]:
        return None

    def check_registry_signal(self, registration_id: str, company_name: str) -> Dict[str, Any]:
        """verify company via single domain search"""
        results = {}
        clean_id = registration_id.lower().strip()
        logger.info(f"registry check: {registration_id}")

        def check_domain(domain: str) -> tuple[str, Dict]:
            res = {"found": False, "verification_method": None, "search_results": []}
            q = f'{domain} {company_name} {registration_id}'
            found, data = self._check_query(q, domain, company_name, clean_id)
            res["search_results"].extend(data)
            if found:
                res["found"] = True
                res["verification_method"] = "name_match"
            return domain, res

        # single domain = no need for threadpool, just run directly
        if len(self.TRUSTED_DOMAINS) == 1:
            domain, res = check_domain(self.TRUSTED_DOMAINS[0])
            results[domain] = res
        else:
            with ThreadPoolExecutor(max_workers=len(self.TRUSTED_DOMAINS)) as ex:
                for future in [ex.submit(check_domain, d) for d in self.TRUSTED_DOMAINS]:
                    domain, res = future.result()
                    results[domain] = res
        return results

    def _check_query(self, query: str, domain: str, name: str, reg_id: str) -> tuple[bool, List[Dict]]:
        """parse search results for match"""
        results = self.scraper.search_web(query, num_results=3)
        for res in results:
            if domain in res.get('link', ''):
                score = self.scraper.calculate_fuzzy_match(name, res.get('title', ''))
                if score > 70:
                    logger.info(f"match: {domain} (score={score})")
                    return True, results
        return False, results

    def verify_by_name(self, name: str) -> List[Dict[str, Any]]:
        return []

class ZaubaProvider(SearchBasedProvider):
    """indian registry - zaubacorp only"""
    TRUSTED_DOMAINS = ["zaubacorp.com"]

    def verify_by_id(self, registration_id: str, company_name: str = "") -> Optional[Dict[str, Any]]:
        return super().verify_by_id(registration_id, company_name)

class OpenCorporatesProvider(SearchBasedProvider):
    """global registry - opencorporates only"""
    TRUSTED_DOMAINS = ["opencorporates.com"]

    def verify_by_id(self, registration_id: str, company_name: str = "") -> Optional[Dict[str, Any]]:
        return super().verify_by_id(registration_id, company_name)
