from typing import Dict, Optional, Any
import logging
import json
from app.engine.providers import ZaubaProvider, OpenCorporatesProvider
from app.engine.pdl_provider import PeopleDataLabsProvider
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

class LookupEngine:
    """
    Orchestrates the selection of appropriate registry providers based on jurisdiction.
    Acts as a router to the specific verification logic.
    """

    def __init__(self):
        self.zauba = ZaubaProvider()
        self.opencorps = OpenCorporatesProvider()
        self.pdl = PeopleDataLabsProvider()

    async def check_registry_presence(self, name: str, country: str, registration_id: str) -> Dict[str, bool]:
        pass

    async def check_registry_and_metadata(self, name: str, country: str, registration_id: Optional[str], linkedin_url: str = None, website: str = None) -> tuple[Dict[str, Any], Dict[str, Any]]:
        # 1. try cache
        # key now allows "None" id
        safe_id = registration_id.lower() if registration_id else "noid"
        key = f"registry:signal:{country.lower()}:{safe_id}:{name.lower()}"
        # if raw := await redis_client.get(key):
        #     try: return json.loads(raw), {}
        #     except: pass

        # 2. registry verification (only if ID provided)
        breakdown = {}
        if registration_id:
            logger.info(f"verifying registry: {registration_id}")
            provider = self._get_provider(country)
            breakdown = provider.check_registry_signal(registration_id, name)
        
        # 3. pdl enrichment
        try:
            logger.info("checking pdl...")
            # Pass empty ID if None
            pdl_data = self.pdl.check_registry_signal(registration_id or "", name, linkedin_url, website)
            breakdown.update(pdl_data)
        except Exception as e:
            logger.error(f"pdl lookup failed: {e}")
        
        # 4. cache result
        # try: await redis_client.set(key, json.dumps(breakdown), ttl=86400)
        # except: pass
            
        return breakdown, {}

    def _get_provider(self, country: str):
        if country.lower() == "india":
            return self.zauba
        return self.opencorps
