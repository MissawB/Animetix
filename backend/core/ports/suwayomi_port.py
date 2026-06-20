from abc import ABC, abstractmethod
from typing import Any, Dict, List


class SuwayomiPort(ABC):

    @abstractmethod
    def get_sources(self) -> List[Dict[str, Any]]:
        """Fetch all installed manga sources from Suwayomi."""
        pass

    @abstractmethod
    def search_manga(self, source_id: str, query: str = "") -> List[Dict[str, Any]]:
        """Search manga or retrieve popular manga from a source on Suwayomi."""
        pass

    @abstractmethod
    def get_manga_details(self, suwayomi_manga_id: str) -> Dict[str, Any]:
        """Fetch details of a manga by its ID from Suwayomi."""
        pass

    @abstractmethod
    def get_chapters(self, suwayomi_manga_id: str) -> List[Dict[str, Any]]:
        """Fetch chapters for a given manga ID from Suwayomi."""
        pass

    @abstractmethod
    def get_pages(self, suwayomi_chapter_id: str) -> List[str]:
        """Fetch page image URLs/paths for a given chapter ID."""
        pass
