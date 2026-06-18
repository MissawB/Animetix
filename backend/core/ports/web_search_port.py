from abc import ABC, abstractmethod
from typing import List, Dict


class WebSearchPort(ABC):
    @abstractmethod
    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Effectue une recherche sur le Web en temps réel."""
        pass

    @abstractmethod
    def get_content(self, url: str) -> str:
        """Récupère et nettoie le contenu d'une page Web."""
        pass
