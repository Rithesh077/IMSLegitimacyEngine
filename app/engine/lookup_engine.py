from typing import Dict, Optional, Any
import logging
import asyncio
from app.engine.providers import ZaubaProvider, OpenCorporatesProvider
from app.engine.pdl_provider import PeopleDataLabsProvider

logger = logging.getLogger(__name__)

class LookupEngine:
    """registry lookups - all searches run in parallel"""

    def __init__(self):
        self.zauba = ZaubaProvider()
        self.opencorps = OpenCorporatesProvider()
        self.pdl = PeopleDataLabsProvider()

    async def check_registry_and_metadata(self, name: str, country: str, registration_id: Optional[str], linkedin_url: str = None, website: str = None) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """run registry + pdl in parallel"""
        async def do_registry():
            if not registration_id: return {}
            provider = self._get_provider(country)
            return await asyncio.to_thread(provider.check_registry_signal, registration_id, name)

        async def do_pdl():
            try:
                return await asyncio.to_thread(self.pdl.check_registry_signal, registration_id or "", name, linkedin_url, website)
            except Exception as e:
                logger.error(f"pdl: {e}")
                return {}

        # run both in parallel
        logger.info(f"parallel lookup: {name}")
        reg_result, pdl_result = await asyncio.gather(do_registry(), do_pdl())
        
        breakdown = reg_result
        breakdown.update(pdl_result)
        return breakdown, {}

    def _get_provider(self, country: str):
        if country.lower() == "india":
            return self.zauba
        return self.opencorps
