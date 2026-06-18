from abc import ABC, abstractmethod
from typing import List, Optional


class SemanticCachePort(ABC):
    @abstractmethod
    def get(self, query: str) -> Optional[str]:
        """Récupère une réponse en cache pour une requête exacte."""
        pass

    @abstractmethod
    def get_semantic(
        self, query_embedding: List[float], threshold: float
    ) -> Optional[str]:
        """Récupère la réponse la plus proche sémantiquement."""
        pass

    @abstractmethod
    def set(self, query: str, query_embedding: List[float], response: str) -> None:
        """Enregistre une réponse en cache."""
        pass
