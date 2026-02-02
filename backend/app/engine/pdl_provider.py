import os
import requests
import logging
from typing import Optional, Dict, Any, List
from app.engine.registry_provider import RegistryProvider

logger = logging.getLogger(__name__)

class PeopleDataLabsProvider(RegistryProvider):
    BASE_URL = "https://api.peopledatalabs.com/v5/company/search"

    def __init__(self):
        self.api_key = os.getenv("PDL_API_KEY")
        if not self.api_key:
            logger.warning("no pdl api key found, skipping lookups")

    def verify_by_id(self, registration_id: str, company_name: str = "") -> Optional[Dict[str, Any]]:
        return None

    def _clean_name(self, name: str) -> str:
        # strip legal suffixes
        suffixes = [
            " private limited", " pvt ltd", " pvt. ltd.", " limited", " ltd", " ltd.", 
            " inc", " inc.", " incorporation", " corp", " corp.", " corporation", 
            " llc", " l.l.c.", " & co", " & co.", " s.a.", " gmbh"
        ]
        clean = name.lower()
        for suffix in suffixes:
            if clean.endswith(suffix):
                clean = clean[:-len(suffix)]
        return clean.strip()

    def check_registry_signal(self, registration_id: str, company_name: str, linkedin_url: str = None, website: str = None) -> Dict[str, Any]:
        matches = self.verify_enriched(company_name, linkedin_url, website)
        return {
            "peopledatalabs.com": {
                "found": len(matches) > 0,
                "verification_method": "pdl_api",
                "search_results": matches
            }
        }

    def verify_by_name(self, name: str) -> List[Dict[str, Any]]:
        return self.verify_enriched(name)

    def verify_enriched(self, name: str, linkedin_url: str = None, website: str = None) -> List[Dict[str, Any]]:
        if not self.api_key: return []
        
        # TODO: parse document logic here if needed for deeper context

        # 1. linkedin (best match)
        if linkedin_url:
            if res := self._execute_pdl_query(f"SELECT * FROM company WHERE linkedin_url = '{linkedin_url}'", "linkedin"):
                return res

        # 2. website (reliable)
        if website:
             if res := self._execute_pdl_query(f"SELECT * FROM company WHERE website = '{website}'", "website"):
                 return res

        # 3. exact name
        if res := self._execute_pdl_query(f"SELECT * FROM company WHERE name = '{name}'", "name_exact"):
            return res
            
        # 4. clean name fallback
        clean = self._clean_name(name)
        if clean != name.lower():
            logger.info(f"retrying with cleaned name: {clean}")
            if res := self._execute_pdl_query(f"SELECT * FROM company WHERE name = '{clean}'", "name_clean"):
                return res

        return []

    def _execute_pdl_query(self, sql_query: str, type: str = "") -> List[Dict[str, Any]]:
        try:
            params = {"sql": sql_query, "size": 1, "pretty": False}
            headers = {"X-Api-Key": self.api_key, "Content-Type": "application/json"}
            
            resp = requests.get(self.BASE_URL, headers=headers, params=params, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if data: 
                    logger.info(f"pdl match via {type}")
                    return data
            
            elif resp.status_code in [401, 402]:
                logger.error(f"pdl api error {resp.status_code}: check keys/credits")
                
        except Exception as e:
            logger.error(f"pdl connection error: {e}")
            
        return []
