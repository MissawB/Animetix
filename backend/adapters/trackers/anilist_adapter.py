import logging
from typing import Any, Dict, List, Optional

import httpx
from core.ports.tracker_port import TrackerPort

logger = logging.getLogger("animetix.trackers")

API_URL = "https://graphql.anilist.co"

SEARCH_QUERY = """
query ($search: String) {
  Page(perPage: 5) {
    media(search: $search, type: MANGA) {
      id
      title { romaji english }
      chapters
    }
  }
}
"""

PROGRESS_QUERY = """
query ($id: Int) {
  Media(id: $id, type: MANGA) {
    mediaListEntry { progress }
  }
}
"""

SAVE_MUTATION = """
mutation ($mediaId: Int, $progress: Int) {
  SaveMediaListEntry(mediaId: $mediaId, progress: $progress, status: CURRENT) {
    id
    progress
  }
}
"""


class AniListAdapter(TrackerPort):
    """Client AniList (GraphQL). Voir `TrackerPort` : rien ne remonte en exception."""

    def _post(self, query: str, variables: Dict[str, Any], token: Optional[str]):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(
                    API_URL,
                    json={"query": query, "variables": variables},
                    headers=headers,
                )
            if res.status_code != 200:
                logger.warning("AniList a répondu %s", res.status_code)
                return None
            body = res.json()
            if "errors" in body:
                logger.warning("Erreurs GraphQL AniList : %s", body["errors"])
                return None
            return body.get("data")
        except Exception as exc:
            logger.warning("AniList injoignable : %s", exc)
            return None

    def search(self, query: str, token: Optional[str]) -> List[Dict[str, Any]]:
        data = self._post(SEARCH_QUERY, {"search": query}, token)
        results: List[Dict[str, Any]] = []
        # La normalisation est DANS le try : un élément inattendu (non-dict)
        # lèverait sinon hors de l'adaptateur, ce que `TrackerPort` interdit —
        # et ferait un 500 sur l'endpoint des liaisons.
        try:
            media = ((data or {}).get("Page") or {}).get("media") or []
            for item in media:
                if not isinstance(item, dict) or "id" not in item:
                    continue
                title = item.get("title")
                title = title if isinstance(title, dict) else {}
                results.append(
                    {
                        "remote_id": str(item["id"]),
                        "title": title.get("romaji") or title.get("english") or "",
                        "chapters": item.get("chapters"),
                    }
                )
        except Exception as exc:
            logger.warning("Réponse AniList inexploitable : %s", exc)
            return []
        return results

    def read_progress(self, remote_id: str, token: str) -> Optional[int]:
        try:
            media_id = int(remote_id)
        except ValueError:
            logger.warning("Invalid remote_id for read_progress: %s", remote_id)
            return None
        data = self._post(PROGRESS_QUERY, {"id": media_id}, token)
        if not isinstance(data, dict):
            # `_post` a déjà renvoyé None : appel en échec, progression inconnue.
            return None
        media = data.get("Media")
        if not isinstance(media, dict):
            return None
        entry = media.get("mediaListEntry")
        if entry is None:
            # La réponse est arrivée et l'œuvre n'est simplement pas encore dans
            # la liste de l'utilisateur : c'est 0, pas « inconnu ». Renvoyer None
            # ici empêcherait toute création d'entrée distante — le cas le plus
            # courant (nouvelle série commencée sur Animetix).
            return 0
        if not isinstance(entry, dict):
            # `mediaListEntry` est présent mais mal formé (liste, scalaire...) :
            # réponse illisible, pas une absence légitime. `None` pour retenter
            # plus tard plutôt que d'écraser une progression distante réelle
            # avec un 0 fabriqué.
            logger.warning("AniList : `mediaListEntry` inattendu (non-dict)")
            return None
        progress = entry.get("progress")
        return progress if isinstance(progress, int) else 0

    def write_progress(self, remote_id: str, progress: int, token: str) -> bool:
        try:
            media_id = int(remote_id)
        except ValueError:
            logger.warning("Invalid remote_id for write_progress: %s", remote_id)
            return False
        data = self._post(
            SAVE_MUTATION, {"mediaId": media_id, "progress": progress}, token
        )
        return bool((data or {}).get("SaveMediaListEntry"))
