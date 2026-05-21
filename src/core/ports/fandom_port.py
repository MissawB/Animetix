from abc import ABC, abstractmethod
from typing import Dict, Any

class FandomPort(ABC):
    @abstractmethod
    def fetch_character_data(self, character_name: str) -> Dict[str, Any]:
        """Fetches character data from VS Battles Wiki."""
        pass
