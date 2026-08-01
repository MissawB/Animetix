import logging
from typing import Any, Dict, List, Optional

from core.ports.manga_progress_repository_port import MangaProgressRepositoryPort

logger = logging.getLogger("animetix.manga")


class MangaProgressService:
    """Progression de lecture par utilisateur.

    La vérité est ici ; Suwayomi ne reçoit qu'un miroir best-effort, car son
    état est global au serveur et injoignable en production.
    """

    def __init__(
        self,
        progress_repository: MangaProgressRepositoryPort,
        suwayomi_adapter=None,
    ):
        self.repo = progress_repository
        self.suwayomi_adapter = suwayomi_adapter

    def get_manga_progress(self, user: Any, manga_id: str) -> Optional[Dict]:
        if self.repo.get_manga(manga_id) is None:
            return None

        chapters = self.repo.list_chapters_with_progress(user, manga_id)
        public = [
            {
                "number": row["number"],
                "is_read": row["is_read"],
                "last_page_read": row["last_page_read"],
                "page_count": row["page_count"],
            }
            for row in chapters
        ]
        return {
            "chapters": public,
            "resume": self._resume_point(chapters),
            "read_count": sum(1 for row in chapters if row["is_read"]),
            "total_count": len(chapters),
        }

    def record_progress(
        self,
        user: Any,
        manga_id: str,
        chapter_number: float,
        last_page_read: int,
        is_read: bool,
    ) -> Optional[Dict]:
        chapter = self.repo.get_chapter(manga_id, chapter_number)
        if chapter is None:
            return None

        previous = self._existing_row(self.repo.get_progress(user, chapter))

        # Monotone : la position ne recule jamais, sauf remise à zéro explicite
        # (repasser le chapitre en non-lu avec last_page_read=0).
        explicit_reset = not is_read and last_page_read == 0
        cursor = (
            last_page_read
            if explicit_reset
            else max(previous["last_page_read"], last_page_read)
        )

        self.repo.upsert_progress(user, chapter, cursor, is_read)

        completed = is_read and not previous["is_read"]
        if completed:
            manga = self.repo.get_manga(manga_id)
            if manga is not None:
                self.repo.set_favorite_last_read(user, manga, chapter_number)

        self._mirror([chapter], is_read, cursor)
        return {
            "number": chapter_number,
            "is_read": is_read,
            "last_page_read": cursor,
            "chapter_completed": completed,
        }

    def set_read(
        self,
        user: Any,
        manga_id: str,
        chapter_numbers: List[float],
        is_read: bool,
    ) -> int:
        chapters = [
            chapter
            for chapter in (
                self.repo.get_chapter(manga_id, number) for number in chapter_numbers
            )
            if chapter is not None
        ]
        if not chapters:
            return 0

        count = self.repo.bulk_set_read(user, chapters, is_read)
        if is_read:
            manga = self.repo.get_manga(manga_id)
            if manga is not None:
                self.repo.set_favorite_last_read(
                    user, manga, max(chapter.number for chapter in chapters)
                )
        self._mirror(chapters, is_read, None)
        return count

    def _existing_row(self, row: Any) -> Dict:
        if row is None:
            return {"last_page_read": 0, "is_read": False}
        return {"last_page_read": row.last_page_read, "is_read": row.is_read}

    def _resume_point(self, chapters: List[Dict]) -> Optional[Dict]:
        started = [
            row
            for row in chapters
            if not row["is_read"] and row["updated_at"] is not None
        ]
        if started:
            row = max(started, key=lambda item: item["updated_at"])
            return {
                "chapter_number": row["number"],
                "last_page_read": row["last_page_read"],
            }

        read_numbers = [row["number"] for row in chapters if row["is_read"]]
        if read_numbers:
            highest = max(read_numbers)
            following = [
                row
                for row in chapters
                if not row["is_read"] and row["number"] > highest
            ]
            if following:
                return {
                    "chapter_number": following[0]["number"],
                    "last_page_read": 0,
                }
        return None

    def _mirror(
        self, chapters: List[Any], is_read: bool, last_page_read: Optional[int]
    ) -> None:
        """Répercute l'état vers Suwayomi. Best-effort : un échec ne remonte pas."""
        if not self.suwayomi_adapter:
            return
        ids = [c.external_id for c in chapters if c.external_id]
        if not ids:
            return
        try:
            self.suwayomi_adapter.update_chapters_read_state(
                ids, is_read=is_read, last_page_read=last_page_read
            )
        except Exception as exc:
            logger.warning(
                "Miroir Suwayomi ignoré pour %s chapitre(s) : %s", len(ids), exc
            )
