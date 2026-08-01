from abc import ABC, abstractmethod
from typing import Any, List, Optional


class TrackerRepositoryPort(ABC):
    """Persistance des liaisons trackers (garde l'ORM hors du domaine).

    L'absence est signalée par ``None`` ; aucune exception ORM ne remonte.
    """

    @abstractmethod
    def get_manga(self, media_id: str) -> Optional[Any]:
        """Le MediaItem Manga, ou ``None`` s'il n'est pas dans le catalogue."""

    @abstractmethod
    def get_connections(self, user: Any) -> List[Any]:
        """Les ``TrackerConnection`` de cet utilisateur (chacune expose
        ``.tracker`` et ``.token``)."""

    @abstractmethod
    def get_links(self, user: Any, manga: Any) -> List[Any]:
        """Les ``MangaTrackerLink`` de cet utilisateur pour cette œuvre."""

    @abstractmethod
    def get_all_links(self, user: Any) -> List[Any]:
        """Toutes les ``MangaTrackerLink`` de cet utilisateur, toutes œuvres
        confondues."""

    @abstractmethod
    def upsert_link(
        self,
        user: Any,
        manga: Any,
        tracker: str,
        remote_id: str,
        remote_title: str,
        status: str,
    ) -> Any:
        """Crée ou met à jour la liaison et renvoie l'enregistrement."""

    @abstractmethod
    def set_remote_progress(self, link: Any, value: Optional[int]) -> None:
        """Aligne la dernière progression distante connue sur ``link``."""

    @abstractmethod
    def delete_link(self, user: Any, manga: Any, tracker: str) -> bool:
        """Supprime la liaison ; ``True`` si une ligne a bien été supprimée."""
