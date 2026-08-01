from typing import Any, List, Optional

from core.ports.manga_progress_repository_port import MangaProgressRepositoryPort


class DjangoMangaProgressRepositoryAdapter(MangaProgressRepositoryPort):
    """Implémentation Django ORM de :class:`MangaProgressRepositoryPort`."""

    def get_manga(self, manga_id: str) -> Optional[Any]:
        from animetix.models import MediaItem

        try:
            return MediaItem.objects.get(external_id=manga_id, media_type="Manga")
        except MediaItem.DoesNotExist:
            return None

    def get_chapter(self, manga_id: str, number: float) -> Optional[Any]:
        from animetix.models import MangaChapter

        try:
            return MangaChapter.objects.get(manga__external_id=manga_id, number=number)
        except MangaChapter.DoesNotExist:
            return None

    def list_chapters_with_progress(self, user: Any, manga_id: str) -> List[dict]:
        from animetix.models import MangaChapter, MangaReadingProgress
        from django.db.models import (
            BooleanField,
            Count,
            IntegerField,
            OuterRef,
            Subquery,
            Value,
        )
        from django.db.models.functions import Coalesce

        progress = MangaReadingProgress.objects.filter(
            user=user, chapter=OuterRef("pk")
        )
        rows = (
            MangaChapter.objects.filter(manga__external_id=manga_id)
            .annotate(
                # distinct=True : sans lui, le JOIN sur les pages multiplierait les lignes.
                pages_known=Count("pages", distinct=True),
                read_flag=Coalesce(
                    Subquery(progress.values("is_read")[:1]),
                    Value(False),
                    output_field=BooleanField(),
                ),
                page_cursor=Coalesce(
                    Subquery(progress.values("last_page_read")[:1]),
                    Value(0),
                    output_field=IntegerField(),
                ),
                touched_at=Subquery(progress.values("updated_at")[:1]),
            )
            .order_by("number")
        )
        return [
            {
                "number": row.number,
                "is_read": row.read_flag,
                "last_page_read": row.page_cursor,
                "page_count": row.pages_known,
                "external_id": row.external_id,
                "updated_at": row.touched_at,
            }
            for row in rows
        ]

    def get_progress(self, user: Any, chapter: Any) -> Optional[Any]:
        from animetix.models import MangaReadingProgress

        return MangaReadingProgress.objects.filter(user=user, chapter=chapter).first()

    def upsert_progress(
        self, user: Any, chapter: Any, last_page_read: int, is_read: bool
    ) -> Any:
        from animetix.models import MangaReadingProgress

        row, _created = MangaReadingProgress.objects.update_or_create(
            user=user,
            chapter=chapter,
            defaults={"last_page_read": last_page_read, "is_read": is_read},
        )
        return row

    def bulk_set_read(self, user: Any, chapters: List[Any], is_read: bool) -> int:
        for chapter in chapters:
            self.upsert_progress(
                user,
                chapter,
                last_page_read=0 if not is_read else self._current_page(user, chapter),
                is_read=is_read,
            )
        return len(chapters)

    def _current_page(self, user: Any, chapter: Any) -> int:
        row = self.get_progress(user, chapter)
        return row.last_page_read if row else 0

    def set_favorite_last_read(
        self, user: Any, manga: Any, chapter_number: float
    ) -> None:
        from animetix.models import FavoriteManga

        favorite, _created = FavoriteManga.objects.get_or_create(user=user, manga=manga)
        if chapter_number > favorite.last_read_chapter:
            favorite.last_read_chapter = chapter_number
            favorite.save(update_fields=["last_read_chapter", "updated_at"])
