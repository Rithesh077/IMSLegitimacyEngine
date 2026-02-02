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
        # Backward compatibility wrapper if needed, but we'll update the orchestrator.
        # Actually, let's keep this signature relevant to its name "check_registry_presence" (signals)
        # and add a new method or just return the dict as before but also cache/store metadata internally?
        # No, better to be explicit. Let's return a Tuple.
        pass

    async def check_registry_and_metadata(self, name: str, country: str, registration_id: str, linkedin_url: str = None, website: str = None) -> tuple[Dict[str, Any], Dict[str, Any]]:
        # 1. try cache
        key = f"registry:signal:{country.lower()}:{registration_id.lower()}:{name.lower()}"
        if raw := await redis_client.get(key):
            try: return json.loads(raw), {}
            except: pass

        # 2. registry verification
        logger.info(f"verifying registry: {registration_id}")
        provider = self._get_provider(country)
        breakdown = provider.check_registry_signal(registration_id, name)
        
        # 3. pdl enrichment (optional but recommended)
        try:
            logger.info("checking pdl...")
            pdl_data = self.pdl.check_registry_signal(registration_id, name, linkedin_url, website)
            breakdown.update(pdl_data)
        except Exception as e:
            logger.error(f"pdl lookup failed: {e}")
        
        # 4. cache result
        try: await redis_client.set(key, json.dumps(breakdown), ttl=86400)
        except: pass
            
        return breakdown, {}

    def _get_provider(self, country: str):
        if country.lower() == "india":
            return self.zauba
        return self.opencorps
