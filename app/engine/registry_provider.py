from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

class RegistryProvider(ABC):
    """
    interface for official registry lookup providers (e.g. zauba, opencorporates)
    supports both id-based lookup (anchor) and name-based search (fallback)
    """

    @abstractmethod
    def verify_by_id(self, registration_id: str, company_name: str = "") -> Optional[Dict[str, Any]]:
        """
        fetches raw company metadata by its unique registration id (cin, ein, gst)
        returns dictionary of metadata if found, else none
        """
        pass

    @abstractmethod
    def verify_by_name(self, name: str) -> List[Dict[str, Any]]:
        """
        searches for company by name on the registry
        returns list of potential matches
        """
        pass
