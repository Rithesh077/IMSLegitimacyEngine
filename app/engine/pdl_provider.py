import os
import requests
import logging
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
from app.engine.registry_provider import RegistryProvider

logger = logging.getLogger(__name__)

class PeopleDataLabsProvider(RegistryProvider):
    """pdl enrichment - parallel queries"""
    BASE_URL = "https://api.peopledatalabs.com/v5/company/search"

    def __init__(self):
        self.api_key = os.getenv("PDL_API_KEY")
        if not self.api_key:
            logger.warning("no pdl api key")

    def verify_by_id(self, registration_id: str, company_name: str = "") -> Optional[Dict[str, Any]]:
        return None

    def _clean_name(self, name: str) -> str:
        suffixes = [" private limited", " pvt ltd", " pvt. ltd.", " limited", " ltd", " ltd.", 
                    " inc", " inc.", " corp", " corp.", " llc", " gmbh"]
        clean = name.lower()
        for s in suffixes:
            if clean.endswith(s): clean = clean[:-len(s)]
        return clean.strip()

    def check_registry_signal(self, registration_id: str, company_name: str, linkedin_url: str = None, website: str = None) -> Dict[str, Any]:
        matches = self.verify_enriched(company_name, linkedin_url, website)
        return {"peopledatalabs.com": {"found": len(matches) > 0, "verification_method": "pdl_api", "search_results": matches}}

    def verify_by_name(self, name: str) -> List[Dict[str, Any]]:
        return self.verify_enriched(name)

    def verify_enriched(self, name: str, linkedin_url: str = None, website: str = None) -> List[Dict[str, Any]]:
        if not self.api_key: return []
        
        # build all queries
        queries = []
        if linkedin_url:
            queries.append((f"SELECT * FROM company WHERE linkedin_url = '{linkedin_url}'", "linkedin"))
        if website:
            queries.append((f"SELECT * FROM company WHERE website = '{website}'", "website"))
        queries.append((f"SELECT * FROM company WHERE name = '{name}'", "name"))
        clean = self._clean_name(name)
        if clean != name.lower():
            queries.append((f"SELECT * FROM company WHERE name = '{clean}'", "clean_name"))
        
        # run all queries in parallel, return first match
        with ThreadPoolExecutor(max_workers=len(queries)) as ex:
            futures = [ex.submit(self._execute_pdl_query, q, t) for q, t in queries]
            for future in futures:
                res = future.result()
                if res: return res
        return []

    def _execute_pdl_query(self, sql_query: str, qtype: str = "") -> List[Dict[str, Any]]:
        try:
            params = {"sql": sql_query, "size": 1, "pretty": False}
            headers = {"X-Api-Key": self.api_key, "Content-Type": "application/json"}
            resp = requests.get(self.BASE_URL, headers=headers, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if data:
                    logger.info(f"pdl: {qtype}")
                    return data
            elif resp.status_code in [401, 402]:
                logger.error(f"pdl auth: {resp.status_code}")
        except Exception as e:
            logger.error(f"pdl: {e}")
        return []
