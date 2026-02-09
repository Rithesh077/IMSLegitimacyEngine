from typing import Dict, Optional, Any
import logging
import asyncio
from app.engine.providers import ZaubaProvider, OpenCorporatesProvider
from app.engine.pdl_provider import PeopleDataLabsProvider

logger = logging.getLogger(__name__)

class LookupEngine:
    """routes registry lookups to appropriate provider based on jurisdiction."""

    def __init__(self):
        self.zauba = ZaubaProvider()
        self.opencorps = OpenCorporatesProvider()
        self.pdl = PeopleDataLabsProvider()

    async def check_registry_and_metadata(self, name: str, country: str, registration_id: Optional[str], linkedin_url: str = None, website: str = None) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """checks registry and enriches with pdl data."""
        breakdown = {}
        
        if registration_id:
            logger.info(f"verifying registry: {registration_id}")
            provider = self._get_provider(country)
            breakdown = await asyncio.to_thread(provider.check_registry_signal, registration_id, name)
        
        try:
            logger.info("checking pdl...")
            pdl_data = await asyncio.to_thread(self.pdl.check_registry_signal, registration_id or "", name, linkedin_url, website)
            breakdown.update(pdl_data)
        except Exception as e:
            logger.error(f"pdl lookup failed: {e}")
        
        return breakdown, {}

    def _get_provider(self, country: str):
        """returns appropriate registry provider for country."""
        if country.lower() == "india":
            return self.zauba
        return self.opencorps
