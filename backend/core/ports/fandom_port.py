from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class FandomPort(ABC):
    @abstractmethod
    def fetch_character_data(
        self, character_name: str, franchise: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetches character data variations from VS Battles Wiki.
        Returns a list of dicts with: name, wikitext, image_url, url, categories.
        """
        pass
