import base64
import logging
from typing import Any, List, Optional

from core.ports.manga_repository_port import MangaRepositoryPort

logger = logging.getLogger("animetix.manga")


class MangaService:
    """
    Service gérant la logique métier des mangas, notamment le chargement dynamique
    des chapitres. Toute la persistance passe par ``MangaRepositoryPort`` (le domaine
    n'importe pas l'ORM Django).
    """

    def __init__(
        self,
        manga_repository: MangaRepositoryPort,
        suwayomi_adapter=None,
    ):
        self.repo = manga_repository
        self.suwayomi_adapter = suwayomi_adapter

    def get_chapters(self, manga_id: str) -> List[Any]:
        """Récupère la liste des chapitres. Déclenche une synchro si nécessaire."""
        chapters = self.repo.get_chapters(manga_id)

        if not chapters:
            logger.info(
                f"📚 No chapters found in DB for manga {manga_id}. Triggering dynamic fetch..."
            )
            # Raccordement dynamique à Suwayomi ou mock
            self._sync_chapters_from_external(manga_id)
            chapters = self.repo.get_chapters(manga_id)

        return chapters

    def get_chapter_details(
        self, manga_id: str, chapter_number: float
    ) -> Optional[Any]:
        """Récupère les détails d'un chapitre (pages)."""
        chapter = self.repo.get_chapter(manga_id, chapter_number)

        if chapter is not None:
            # Si le chapitre n'a pas de pages, on tente de les charger
            if not self.repo.chapter_has_pages(chapter):
                logger.info(
                    f"📄 No pages found for chapter {chapter_number} of manga {manga_id}. Fetching..."
                )
                self._sync_pages_from_external(chapter)
            return chapter

        # Tenter de synchroniser si le manga existe
        if self.repo.get_manga(manga_id) is not None:
            self._sync_chapters_from_external(manga_id)
            return self.repo.get_chapter(manga_id, chapter_number)
        return None

    def _sync_chapters_from_external(self, manga_id: str):
        """
        Récupère les chapitres depuis un backend externe (Suwayomi ou Mock).
        """
        manga = self.repo.get_manga(manga_id)
        if manga is None:
            logger.error(
                f"❌ Cannot sync chapters: Manga {manga_id} not found in catalog."
            )
            return

        if manga_id.startswith("suwayomi:") and self.suwayomi_adapter:
            # Format: suwayomi:<source_id>:<suwayomi_manga_id>
            parts = manga_id.split(":")
            if len(parts) >= 3:
                suwayomi_manga_id = parts[2]
                logger.info(
                    f"Syncing chapters from Suwayomi for manga {suwayomi_manga_id}"
                )
                chapters_data = self.suwayomi_adapter.get_chapters(suwayomi_manga_id)
                new_chapters = []
                for ch in chapters_data:
                    _chapter, created = self.repo.upsert_chapter(
                        manga,
                        float(ch.get("chapterNumber", 0.0) or 0.0),
                        ch.get("name", f"Chapitre {ch.get('chapterNumber')}"),
                        external_id=str(ch.get("id")),
                    )
                    if created:
                        new_chapters.append(_chapter)
                logger.info(
                    f"✅ Synced {len(new_chapters)} chapters from Suwayomi for {manga.title}"
                )
                return

        # Mock: Création de 3 chapitres de démo si rien n'existe
        new_chapters = []
        for i in range(1, 4):
            _chapter, created = self.repo.upsert_chapter(
                manga, float(i), f"Chapitre {i} : L'éveil du Nexus"
            )
            if created:
                new_chapters.append(_chapter)

        logger.info(f"✅ Synced {len(new_chapters)} new chapters for {manga.title}")

    def _sync_pages_from_external(self, chapter: Any):
        """
        Récupère les pages depuis Suwayomi ou génère des placeholders.
        """
        if (
            chapter.manga.external_id.startswith("suwayomi:")
            and self.suwayomi_adapter
            and chapter.external_id
        ):
            logger.info(
                f"Syncing pages from Suwayomi for chapter {chapter.external_id}"
            )
            pages_data = self.suwayomi_adapter.get_pages(chapter.external_id)
            pages = []
            for idx, p_url in enumerate(pages_data):
                # Generates backend image proxy URL
                encoded_url = base64.b64encode(p_url.encode("utf-8")).decode("utf-8")
                proxy_url = (
                    f"/api/v1/media/Manga/suwayomi-image/?page_url={encoded_url}"
                )
                page, _created = self.repo.upsert_page(chapter, idx + 1, proxy_url)
                pages.append(page)
            logger.info(
                f"✅ Synced {len(pages)} pages from Suwayomi for chapter {chapter.number}"
            )
            return

        # Mock: Création de 5 pages de démo
        page_urls = [
            f"https://picsum.photos/seed/animetix_{chapter.manga.external_id}_{chapter.number}_{p}/800/1200"
            for p in range(1, 6)
        ]

        pages = []
        for idx, url in enumerate(page_urls):
            page, _created = self.repo.upsert_page(chapter, idx + 1, url)
            pages.append(page)

        logger.info(f"✅ Synced {len(pages)} pages for {chapter}")
