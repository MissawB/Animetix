import logging
from typing import List, Optional

from animetix.models import MangaChapter, MangaPage, MediaItem

logger = logging.getLogger("animetix.manga")


class MangaService:
    """
    Service gérant la logique métier des mangas, notamment le chargement dynamique des chapitres.
    """

    def get_chapters(self, manga_id: str) -> List[MangaChapter]:
        """Récupère la liste des chapitres. Déclenche une synchro si nécessaire."""
        chapters = list(
            MangaChapter.objects.filter(manga__external_id=manga_id).order_by("number")
        )

        if not chapters:
            logger.info(
                f"📚 No chapters found in DB for manga {manga_id}. Triggering dynamic fetch..."
            )
            # Ici, on simule un raccordement à un backend réel (ex: scraper ou API partenaire)
            self._sync_chapters_from_external(manga_id)
            chapters = list(
                MangaChapter.objects.filter(manga__external_id=manga_id).order_by(
                    "number"
                )
            )

        return chapters

    def get_chapter_details(
        self, manga_id: str, chapter_number: float
    ) -> Optional[MangaChapter]:
        """Récupère les détails d'un chapitre (pages)."""
        try:
            chapter = MangaChapter.objects.get(
                manga__external_id=manga_id, number=chapter_number
            )

            # Si le chapitre n'a pas de pages, on tente de les charger
            if not chapter.pages.exists():
                logger.info(
                    f"📄 No pages found for chapter {chapter_number} of manga {manga_id}. Fetching..."
                )
                self._sync_pages_from_external(chapter)

            return chapter
        except MangaChapter.DoesNotExist:
            # Tenter de synchroniser si le manga existe
            if MediaItem.objects.filter(
                external_id=manga_id, media_type="Manga"
            ).exists():
                self._sync_chapters_from_external(manga_id)
                try:
                    return MangaChapter.objects.get(
                        manga__external_id=manga_id, number=chapter_number
                    )
                except MangaChapter.DoesNotExist:
                    return None
            return None

    def _sync_chapters_from_external(self, manga_id: str):
        """
        Simule la récupération de chapitres depuis un backend réel.
        En production, cela appellerait un ScraperWorker ou une API externe.
        """
        try:
            manga = MediaItem.objects.get(external_id=manga_id, media_type="Manga")

            # Mock: Création de 3 chapitres de démo si rien n'existe
            new_chapters = []
            for i in range(1, 4):
                chapter, created = MangaChapter.objects.get_or_create(
                    manga=manga,
                    number=float(i),
                    defaults={"title": f"Chapitre {i} : L'éveil du Nexus"},
                )
                if created:
                    new_chapters.append(chapter)

            logger.info(f"✅ Synced {len(new_chapters)} new chapters for {manga.title}")

        except MediaItem.DoesNotExist:
            logger.error(
                f"❌ Cannot sync chapters: Manga {manga_id} not found in catalog."
            )

    def _sync_pages_from_external(self, chapter: MangaChapter):
        """
        Simule la récupération des pages d'un chapitre.
        Utilise des placeholders réalistes pour le prototype.
        """
        # Mock: Création de 5 pages de démo
        # Note: Dans un vrai système, les URLs viendraient d'un CDN ou d'un service de stockage
        page_urls = [
            f"https://picsum.photos/seed/animetix_{chapter.manga.external_id}_{chapter.number}_{p}/800/1200"
            for p in range(1, 6)
        ]

        pages = []
        for idx, url in enumerate(page_urls):
            page, created = MangaPage.objects.get_or_create(
                chapter=chapter, number=idx + 1, defaults={"image_url": url}
            )
            pages.append(page)

        logger.info(f"✅ Synced {len(pages)} pages for {chapter}")
