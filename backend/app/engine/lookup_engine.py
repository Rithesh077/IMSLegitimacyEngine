from typing import Dict, Optional
import logging
import json
from app.engine.providers import ZaubaProvider, OpenCorporatesProvider
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

    async def check_registry_presence(self, name: str, country: str, registration_id: str) -> Dict[str, bool]:
        """
        Delegates the verification request to the country-specific provider.
        Returns a dictionary mapping registry domains to boolean verification status.
        Includes Redis caching to avoid redundant expensive search queries.
        """
        # 1. Check Cache
        cache_key = f"registry:signal:{country.lower()}:{registration_id.lower()}:{name.lower()}"
        cached_data = await redis_client.get(cache_key)
        
        if cached_data:
            logger.info(f"Cache Hit for {registration_id}")
            try:
                return json.loads(cached_data)
            except json.JSONDecodeError:
                logger.warning("Failed to decode cached data, re-fetching...")

        # 2. Fetch from Provider
        logger.info(f"Cache Miss. Fetching registry signals for {registration_id}...")
        provider = self._get_provider(country)
        
        # Note: Provider logic is currently synchronous (requests/bs4)
        # In a high-concurrency production env, we might want to run this in an executor.
        # For now, this is acceptable for the V2 pipeline scope.
        breakdown = provider.check_registry_signal(registration_id, name)
        
        # 3. Write to Cache (TTL: 24 hours)
        try:
            await redis_client.set(cache_key, json.dumps(breakdown), ttl=86400)
        except Exception as e:
            logger.error(f"Failed to cache registry signals: {e}")

        return breakdown

    def _get_provider(self, country: str):
        if country.lower() == "india":
            return self.zauba
        return self.opencorps
