from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class FandomPort(ABC):
    @abstractmethod
    def fetch_character_data(self, character_name: str, franchise: Optional[str] = None) -> Dict[str, Any]:
        """Fetches character data from VS Battles Wiki."""
        pass
