import logging
from typing import Any, Dict, List, Optional

from core.ports.tracker_repository_port import TrackerRepositoryPort

logger = logging.getLogger("animetix.trackers")


class MangaTrackerService:
    """Lie une œuvre à son entrée chez un tracker, et pousse la progression.

    Deux règles portent tout : une liaison non confirmée ne pousse rien, et une
    poussée ne fait jamais reculer le compteur distant.
    """

    def __init__(self, repository: TrackerRepositoryPort, adapters: Dict[str, Any]):
        self.repo = repository
        self.adapters = adapters

    def search(self, user: Any, tracker: str, query: str) -> List[Dict[str, Any]]:
        adapter = self.adapters.get(tracker)
        if adapter is None:
            return []
        token = self._token(user, tracker)
        return adapter.search(query, token)

    def suggest(self, user: Any, media_id: str) -> List[Any]:
        manga = self.repo.get_manga(media_id)
        if manga is None:
            return []

        existing = {link.tracker for link in self.repo.get_links(user, manga)}
        created = []
        for conn in self.repo.get_connections(user):
            if conn.tracker in existing:
                continue
            adapter = self.adapters.get(conn.tracker)
            if adapter is None:
                continue
            results = adapter.search(manga.title, conn.token)
            if not results:
                continue
            best = results[0]
            created.append(
                self.repo.upsert_link(
                    user,
                    manga,
                    conn.tracker,
                    best["remote_id"],
                    best.get("title") or "",
                    "suggested",
                )
            )
        return created

    def confirm(
        self, user: Any, media_id: str, tracker: str, remote_id: str
    ) -> Optional[Any]:
        manga = self.repo.get_manga(media_id)
        adapter = self.adapters.get(tracker)
        if manga is None or adapter is None:
            return None

        title = ""
        for link in self.repo.get_links(user, manga):
            if link.tracker == tracker and link.remote_id == remote_id:
                title = link.remote_title
        link = self.repo.upsert_link(
            user, manga, tracker, remote_id, title, "confirmed"
        )

        token = self._token(user, tracker)
        if token:
            self.repo.set_remote_progress(
                link, adapter.read_progress(remote_id, token=token)
            )
        return link

    def unlink(self, user: Any, media_id: str, tracker: str) -> bool:
        manga = self.repo.get_manga(media_id)
        if manga is None:
            return False
        return self.repo.delete_link(user, manga, tracker)

    def push(self, user: Any, media_id: str, progress: int) -> Dict[str, Any]:
        manga = self.repo.get_manga(media_id)
        if manga is None:
            return {}

        results: Dict[str, Any] = {}
        for link in self.repo.get_links(user, manga):
            if link.status != "confirmed":
                continue
            adapter = self.adapters.get(link.tracker)
            token = self._token(user, link.tracker)
            if adapter is None or not token:
                continue

            remote = link.remote_progress
            if remote is None:
                # Inconnue : on retente la lecture, mais on n'écrit jamais à l'aveugle.
                remote = adapter.read_progress(link.remote_id, token=token)
                self.repo.set_remote_progress(link, remote)
                if remote is None:
                    results[link.tracker] = {
                        "success": False,
                        "error": "Remote progress unknown",
                    }
                    continue

            if progress <= remote:
                results[link.tracker] = {"success": True, "skipped": "not ahead"}
                continue

            ok = adapter.write_progress(link.remote_id, progress, token=token)
            if ok:
                self.repo.set_remote_progress(link, progress)
            results[link.tracker] = {"success": ok}
        return results

    def list_links(self, user: Any, media_id: str) -> List[Any]:
        manga = self.repo.get_manga(media_id)
        if manga is None:
            return []
        return self.repo.get_links(user, manga)

    def list_all_links(self, user: Any) -> List[Any]:
        return self.repo.get_all_links(user)

    def connected_trackers(self, user: Any) -> List[str]:
        return [conn.tracker for conn in self.repo.get_connections(user)]

    def _token(self, user: Any, tracker: str) -> Optional[str]:
        for conn in self.repo.get_connections(user):
            if conn.tracker == tracker:
                return conn.token
        return None
