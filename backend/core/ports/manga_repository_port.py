from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple


class MangaRepositoryPort(ABC):
    """Persistence port for manga chapters/pages (keeps the ORM out of the domain).

    Methods return the persisted records as opaque objects (the adapter owns the
    concrete type, e.g. Django models, so they can still be serialized downstream)
    and never raise ORM-specific ``DoesNotExist`` — absence is signalled by ``None``.
    """

    @abstractmethod
    def get_chapters(self, manga_id: str) -> List[Any]:
        """Return the manga's chapters ordered by number (empty list if none)."""

    @abstractmethod
    def get_chapter(self, manga_id: str, number: float) -> Optional[Any]:
        """Return a single chapter, or ``None`` if it does not exist."""

    @abstractmethod
    def chapter_has_pages(self, chapter: Any) -> bool:
        """Whether the given chapter already has pages persisted."""

    @abstractmethod
    def get_manga(self, manga_id: str) -> Optional[Any]:
        """Return the Manga media item, or ``None`` if not in the catalog."""

    @abstractmethod
    def upsert_chapter(
        self,
        manga: Any,
        number: float,
        title: str,
        external_id: Optional[str] = None,
    ) -> Tuple[Any, bool]:
        """Get-or-create a chapter; returns ``(chapter, created)``."""

    @abstractmethod
    def upsert_page(
        self, chapter: Any, number: int, image_url: str
    ) -> Tuple[Any, bool]:
        """Get-or-create a page; returns ``(page, created)``."""
