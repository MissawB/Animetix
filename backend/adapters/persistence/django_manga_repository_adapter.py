from typing import Any, List, Optional, Tuple

from core.ports.manga_repository_port import MangaRepositoryPort


class DjangoMangaRepositoryAdapter(MangaRepositoryPort):
    """Django ORM implementation of :class:`MangaRepositoryPort`."""

    def get_chapters(self, manga_id: str) -> List[Any]:
        from animetix.models import MangaChapter

        return list(
            MangaChapter.objects.filter(manga__external_id=manga_id).order_by("number")
        )

    def get_chapter(self, manga_id: str, number: float) -> Optional[Any]:
        from animetix.models import MangaChapter

        try:
            return MangaChapter.objects.get(manga__external_id=manga_id, number=number)
        except MangaChapter.DoesNotExist:
            return None

    def chapter_has_pages(self, chapter: Any) -> bool:
        return chapter.pages.exists()

    def get_manga(self, manga_id: str) -> Optional[Any]:
        from animetix.models import MediaItem

        try:
            return MediaItem.objects.get(external_id=manga_id, media_type="Manga")
        except MediaItem.DoesNotExist:
            return None

    def upsert_chapter(
        self,
        manga: Any,
        number: float,
        title: str,
        external_id: Optional[str] = None,
    ) -> Tuple[Any, bool]:
        from animetix.models import MangaChapter

        defaults: dict = {"title": title}
        if external_id is not None:
            defaults["external_id"] = external_id
        return MangaChapter.objects.get_or_create(
            manga=manga, number=number, defaults=defaults
        )

    def upsert_page(
        self, chapter: Any, number: int, image_url: str
    ) -> Tuple[Any, bool]:
        from animetix.models import MangaPage

        return MangaPage.objects.get_or_create(
            chapter=chapter, number=number, defaults={"image_url": image_url}
        )
