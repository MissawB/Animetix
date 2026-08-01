import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx
from core.ports.tracker_port import TrackerPort

logger = logging.getLogger("animetix.trackers")

JIKAN_SEARCH = "https://api.jikan.moe/v4/manga?q={query}&limit=5"
MAL_MANGA = "https://api.myanimelist.net/v2/manga/{remote_id}"


class MyAnimeListAdapter(TrackerPort):
    """Client MyAnimeList.

    La recherche passe par Jikan, qui est public : l'API v2 de MAL exige un jeton
    même pour chercher, et le code historique faisait déjà ce choix. Lecture et
    écriture, elles, passent par l'API v2 authentifiée.
    """

    def search(self, query: str, token: Optional[str]) -> List[Dict[str, Any]]:
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(JIKAN_SEARCH.format(query=quote(query)))
            if res.status_code != 200:
                logger.warning("Jikan a répondu %s", res.status_code)
                return []
            entries = res.json().get("data") or []
        except Exception as exc:
            logger.warning("Jikan injoignable : %s", exc)
            return []
        results = []
        for entry in entries:
            if "mal_id" not in entry:
                continue
            results.append(
                {
                    "remote_id": str(entry["mal_id"]),
                    "title": entry.get("title") or "",
                    "chapters": entry.get("chapters"),
                }
            )
        return results

    def read_progress(self, remote_id: str, token: str) -> Optional[int]:
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(
                    MAL_MANGA.format(remote_id=remote_id) + "?fields=my_list_status",
                    headers={"Authorization": f"Bearer {token}"},
                )
            if res.status_code != 200:
                logger.warning("MyAnimeList a répondu %s en lecture", res.status_code)
                return None
            body = res.json()
            status = body.get("my_list_status") if isinstance(body, dict) else None
        except Exception as exc:
            logger.warning("MyAnimeList injoignable : %s", exc)
            return None
        if not isinstance(status, dict):
            # La réponse est arrivée sans `my_list_status` : l'œuvre n'est pas
            # encore dans la liste de l'utilisateur. C'est 0, pas « inconnu » —
            # `None` est réservé aux vrais échecs (non-200, transport), sans
            # quoi une série jamais listée ne serait jamais synchronisée.
            return 0
        read = status.get("num_chapters_read")
        return read if isinstance(read, int) else 0

    def write_progress(self, remote_id: str, progress: int, token: str) -> bool:
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.patch(
                    MAL_MANGA.format(remote_id=remote_id) + "/my_list_status",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    data={"num_chapters_read": progress, "status": "reading"},
                )
            return res.status_code == 200
        except Exception as exc:
            logger.warning("MyAnimeList injoignable en écriture : %s", exc)
            return False
