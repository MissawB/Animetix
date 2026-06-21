import logging

from django.db.models import Max

from animetix.containers import get_container
from animetix.models import MangaChapter, MediaItem, Notification
from animetix.tasks_registry import register_task

logger = logging.getLogger("animetix.manga_tasks")


@register_task("check_manga_updates_task")
def check_manga_updates_task():
    """
    Periodic task to check for updates on all favorited/tracked mangas.
    """
    logger.info("Starting background manga updates check...")

    # 1. Query all unique mangas currently favorited by any user
    favorited_mangas = MediaItem.objects.filter(
        media_type="Manga", favorited_by__isnull=False
    ).distinct()

    logger.info(f"Found {favorited_mangas.count()} favorited mangas to check.")

    container = get_container()
    suwayomi_adapter = container.persistence.suwayomi_adapter()

    new_chapters_total = 0

    for manga in favorited_mangas:
        logger.info(
            f"Checking updates for manga: {manga.title} (ID: {manga.external_id})"
        )

        # Check if it is a Suwayomi manga
        if manga.external_id.startswith("suwayomi:"):
            if not suwayomi_adapter:
                logger.warning(
                    "Suwayomi adapter not configured, skipping Suwayomi manga check."
                )
                continue

            try:
                # Format: suwayomi:<source_id>:<suwayomi_manga_id>
                parts = manga.external_id.split(":")
                if len(parts) < 3:
                    logger.warning(
                        f"Invalid external_id format for manga: {manga.external_id}"
                    )
                    continue

                suwayomi_manga_id = parts[2]

                # Get current chapter numbers in database
                existing_numbers = set(
                    MangaChapter.objects.filter(manga=manga).values_list(
                        "number", flat=True
                    )
                )

                # Fetch chapters from Suwayomi
                chapters_data = suwayomi_adapter.get_chapters(suwayomi_manga_id)

                for ch in chapters_data:
                    ch_num = float(ch.get("chapterNumber", 0.0) or 0.0)
                    if ch_num not in existing_numbers:
                        # Create chapter
                        new_chapter = MangaChapter.objects.create(
                            manga=manga,
                            number=ch_num,
                            title=ch.get("name", f"Chapitre {ch_num}"),
                            external_id=str(ch.get("id")),
                        )
                        new_chapters_total += 1
                        logger.info(f"New chapter found: {manga.title} - Ch.{ch_num}")

                        # Notify all users who favorited this manga
                        for fav in manga.favorited_by.all():
                            Notification.objects.create(
                                user=fav.user,
                                title="Nouveau chapitre disponible !",
                                message=f"Le chapitre {ch_num} de '{manga.title}' ({new_chapter.title}) est maintenant disponible.",
                                notification_type="info",
                                link=f"/media/manga/{manga.external_id}/{ch_num}/",
                            )
            except Exception as e:
                logger.error(
                    f"Error checking Suwayomi updates for manga {manga.title}: {e}",
                    exc_info=True,
                )

        else:
            # Simulated/mock manga updates for local testing/CI
            try:
                # Find maximum chapter number
                max_num = (
                    MangaChapter.objects.filter(manga=manga).aggregate(Max("number"))[
                        "number__max"
                    ]
                    or 0.0
                )
                new_num = max_num + 1.0

                new_chapter = MangaChapter.objects.create(
                    manga=manga,
                    number=new_num,
                    title=f"Chapitre {new_num} (Mock)",
                )
                new_chapters_total += 1
                logger.info(f"Simulated new chapter: {manga.title} - Ch.{new_num}")

                # Notify all users who favorited this manga
                for fav in manga.favorited_by.all():
                    Notification.objects.create(
                        user=fav.user,
                        title="Nouveau chapitre disponible !",
                        message=f"Le chapitre {new_num} de '{manga.title}' ({new_chapter.title}) est maintenant disponible.",
                        notification_type="info",
                        link=f"/media/manga/{manga.external_id}/{new_num}/",
                    )
            except Exception as e:
                logger.error(
                    f"Error checking simulated updates for manga {manga.title}: {e}",
                    exc_info=True,
                )

    logger.info(
        f"Background updates check completed. Found {new_chapters_total} new chapters."
    )
    return f"Synced {new_chapters_total} new chapters."
