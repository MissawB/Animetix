"""Poussée de la progression manga vers les trackers tiers (AniList, MyAnimeList).

Extrait de ``MangaChapterSyncView`` pour être réutilisable : la progression
enregistrée par le lecteur déclenche la même synchronisation.
"""

from animetix_project.logging_config import get_logger

logger = get_logger("animetix.api")


def push_manga_progress_to_trackers(user, manga, media_id: str, progress: int) -> dict:
    """Pousse ``progress`` vers les liaisons CONFIRMÉES de cette œuvre.

    Sans liaison confirmée, ne pousse rien : deviner l'œuvre par son titre
    mettait silencieusement à jour la mauvaise entrée sur un titre ambigu.
    Ne lève jamais — un tracker en panne ne doit pas transformer une lecture
    réussie en erreur.
    """
    try:
        from ..containers import get_container

        service = get_container().core.manga_tracker_service()
        return service.push(user, media_id, progress)
    except Exception:
        logger.warning("Poussée trackers échouée pour %s ch.%s", media_id, progress)
        return {}
