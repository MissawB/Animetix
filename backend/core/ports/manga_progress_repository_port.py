from abc import ABC, abstractmethod
from typing import Any, List, Optional


class MangaProgressRepositoryPort(ABC):
    """Persistance de la progression de lecture (garde l'ORM hors du domaine).

    L'absence est signalée par ``None`` ; aucune exception ORM ne remonte.
    """

    @abstractmethod
    def get_manga(self, manga_id: str) -> Optional[Any]:
        """Le MediaItem Manga, ou ``None`` s'il n'est pas dans le catalogue."""

    @abstractmethod
    def get_chapter(self, manga_id: str, number: float) -> Optional[Any]:
        """Un chapitre précis, ou ``None``."""

    @abstractmethod
    def list_chapters_with_progress(self, user: Any, manga_id: str) -> List[dict]:
        """Tous les chapitres du manga, enrichis de la progression de cet
        utilisateur et du nombre de pages connues, triés par numéro croissant."""

    @abstractmethod
    def get_progress(self, user: Any, chapter: Any) -> Optional[Any]:
        """La progression de cet utilisateur sur ce chapitre, ou ``None``.

        Le domaine ne doit pas traverser les relations ORM lui-même : c'est ce
        que cette méthode évite.
        """

    @abstractmethod
    def upsert_progress(
        self, user: Any, chapter: Any, last_page_read: int, is_read: bool
    ) -> Any:
        """Crée ou met à jour la progression et renvoie l'enregistrement."""

    @abstractmethod
    def bulk_set_read(self, user: Any, chapters: List[Any], is_read: bool) -> int:
        """Marque plusieurs chapitres lus/non lus ; renvoie le nombre traité."""

    @abstractmethod
    def set_favorite_last_read(
        self, user: Any, manga: Any, chapter_number: float
    ) -> None:
        """Aligne ``FavoriteManga.last_read_chapter`` (jamais à la baisse)."""
