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
        media = ((data or {}).get("Page") or {}).get("media") or []
        return [
            {
                "remote_id": str(item["id"]),
                "title": (item.get("title") or {}).get("romaji")
                or (item.get("title") or {}).get("english")
                or "",
                "chapters": item.get("chapters"),
            }
            for item in media
        ]

    def read_progress(self, remote_id: str, token: str) -> Optional[int]:
        data = self._post(PROGRESS_QUERY, {"id": int(remote_id)}, token)
        entry = ((data or {}).get("Media") or {}).get("mediaListEntry")
        return entry.get("progress") if entry else None

    def write_progress(self, remote_id: str, progress: int, token: str) -> bool:
        data = self._post(
            SAVE_MUTATION, {"mediaId": int(remote_id), "progress": progress}, token
        )
        return bool((data or {}).get("SaveMediaListEntry"))
