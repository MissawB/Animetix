from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class TrackerPort(ABC):
    """Contrat d'un tracker tiers (AniList, MyAnimeList).

    Aucune méthode ne lève : une indisponibilité se traduit par une liste vide,
    ``None`` ou ``False``. L'appelant décide quoi en faire — un tracker en panne
    ne doit jamais faire échouer une écriture de progression locale.
    """

    @abstractmethod
    def search(self, query: str, token: Optional[str]) -> List[Dict[str, Any]]:
        """Œuvres correspondantes : ``[{remote_id, title, chapters}]`` (vide si aucune)."""

    @abstractmethod
    def read_progress(self, remote_id: str, token: str) -> Optional[int]:
        """Progression enregistrée chez le tracker, ou ``None`` si inconnue/illisible."""

    @abstractmethod
    def write_progress(self, remote_id: str, progress: int, token: str) -> bool:
        """Écrit la progression ; ``False`` si l'écriture a échoué."""
