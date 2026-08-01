from typing import Any, List, Optional

from core.ports.tracker_repository_port import TrackerRepositoryPort


class DjangoTrackerRepositoryAdapter(TrackerRepositoryPort):
    """Implémentation Django ORM de :class:`TrackerRepositoryPort`."""

    def get_manga(self, media_id: str) -> Optional[Any]:
        from animetix.models import MediaItem

        try:
            return MediaItem.objects.get(external_id=media_id, media_type="Manga")
        except MediaItem.DoesNotExist:
            return None

    def get_connections(self, user: Any) -> List[Any]:
        from animetix.models import TrackerConnection

        return list(TrackerConnection.objects.filter(user=user))

    def get_links(self, user: Any, manga: Any) -> List[Any]:
        from animetix.models import MangaTrackerLink

        return list(MangaTrackerLink.objects.filter(user=user, manga=manga))

    def get_all_links(self, user: Any) -> List[Any]:
        from animetix.models import MangaTrackerLink

        return list(MangaTrackerLink.objects.filter(user=user))

    def upsert_link(
        self,
        user: Any,
        manga: Any,
        tracker: str,
        remote_id: str,
        remote_title: str,
        status: str,
    ) -> Any:
        from animetix.models import MangaTrackerLink

        link, _created = MangaTrackerLink.objects.update_or_create(
            user=user,
            manga=manga,
            tracker=tracker,
            defaults={
                "remote_id": remote_id,
                "remote_title": remote_title,
                "status": status,
            },
        )
        return link

    def set_remote_progress(self, link: Any, value: Optional[int]) -> None:
        link.remote_progress = value
        link.save(update_fields=["remote_progress", "updated_at"])

    def delete_link(self, user: Any, manga: Any, tracker: str) -> bool:
        from animetix.models import MangaTrackerLink

        deleted, _ = MangaTrackerLink.objects.filter(
            user=user, manga=manga, tracker=tracker
        ).delete()
        return deleted > 0
