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
        self,
        user: Any,
        media_id: str,
        tracker: str,
        remote_id: str,
        remote_title: str = "",
    ) -> Optional[Any]:
        manga = self.repo.get_manga(media_id)
        adapter = self.adapters.get(tracker)
        if manga is None or adapter is None:
            return None

        # Le titre fourni par l'appelant fait foi : c'est le seul disponible
        # quand l'utilisateur *corrige* une proposition (le `remote_id` change,
        # donc aucune liaison en base ne le porte). Sans lui, la liaison
        # confirmée s'affichait sans nom d'œuvre — précisément là où la
        # vérification visuelle compte le plus.
        title = remote_title or ""
        for link in self.repo.get_links(user, manga):
            if not title and link.tracker == tracker and link.remote_id == remote_id:
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
            try:
                outcome = self._push_one(user, link, progress)
            except Exception as exc:
                # Défense en profondeur : les adaptateurs ne sont pas censés
                # lever (ils renvoient [], None, False), mais un tracker en
                # panne ne doit jamais empêcher les autres d'être tentés.
                logger.warning(
                    "Push %s a levé pour le lien %s: %s",
                    link.tracker,
                    link.remote_id,
                    exc,
                )
                outcome = {"success": False, "error": str(exc)}
            if outcome is not None:
                results[link.tracker] = outcome
        return results

    def _push_one(
        self, user: Any, link: Any, progress: int
    ) -> Optional[Dict[str, Any]]:
        adapter = self.adapters.get(link.tracker)
        token = self._token(user, link.tracker)
        if adapter is None or not token:
            return None

        remote = link.remote_progress
        if remote is None:
            # Inconnue : on retente la lecture, mais on n'écrit jamais à l'aveugle.
            remote = adapter.read_progress(link.remote_id, token=token)
            self.repo.set_remote_progress(link, remote)
            if remote is None:
                return {"success": False, "error": "Remote progress unknown"}

        if progress <= remote:
            return {"success": True, "skipped": "not ahead"}

        ok = adapter.write_progress(link.remote_id, progress, token=token)
        if ok:
            self.repo.set_remote_progress(link, progress)
        return {"success": ok}

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
