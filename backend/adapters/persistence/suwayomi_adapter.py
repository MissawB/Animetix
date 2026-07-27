import logging
from typing import Any, Dict, List, Optional

import httpx
from core.config import settings
from core.ports.suwayomi_port import SuwayomiPort

logger = logging.getLogger("animetix.suwayomi")


class SuwayomiUnavailableError(Exception):
    """Le serveur Suwayomi/Tachidesk est injoignable (non démarré ou mauvaise URL).

    Distinct d'une réponse vide (serveur joignable, sans sources/extensions) : les
    vues peuvent ainsi renvoyer un 503 explicite au lieu d'une liste vide muette.
    """


class SuwayomiAdapter(SuwayomiPort):

    def __init__(self):
        self.url = f"{settings.SUWAYOMI_URL.rstrip('/')}/api/graphql"
        self.headers = {"Content-Type": "application/json"}
        if settings.SUWAYOMI_PASSWORD:
            self.headers["Authorization"] = f"Bearer {settings.SUWAYOMI_PASSWORD}"

    def _query(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(
                    self.url,
                    json={"query": query, "variables": variables or {}},
                    headers=self.headers,
                )
                res.raise_for_status()
                data = res.json()
                if "errors" in data:
                    logger.error(f"GraphQL Errors: {data['errors']}")
                    return {}
                return data.get("data", {})
        except httpx.RequestError as e:
            # Erreur de transport (connexion refusée / timeout) : le serveur
            # Suwayomi n'est pas joignable (non démarré ou mauvaise URL).
            logger.warning(f"Suwayomi unreachable at {self.url}: {e}")
            raise SuwayomiUnavailableError(str(e)) from e
        except Exception as e:
            logger.error(f"Failed to query Suwayomi at {self.url}: {e}")
            return {}

    def get_sources(self) -> List[Dict[str, Any]]:
        q = """
        query {
          sources {
            nodes {
              id
              name
              lang
            }
          }
        }
        """
        data = self._query(q)
        return data.get("sources", {}).get("nodes", [])

    def search_manga(
        self, source_id: str, query: str = "", page: int = 1
    ) -> Dict[str, Any]:
        # Suwayomi ≥ v1.x : `fetchSourceManga` est une MUTATION à `input:{}` (et le
        # type enum est `FetchSourceMangaType`). L'ancienne forme
        # `query { fetchSourceManga(source: ...) }` renvoie "Field undefined" ->
        # aucun manga affiché dans l'onglet Catalog.
        # Retourne {mangas, hasNextPage} pour permettre la pagination du catalogue.
        q = """
        mutation Search($source: LongString!, $query: String, $type: FetchSourceMangaType!, $page: Int!) {
          fetchSourceManga(input: { source: $source, query: $query, type: $type, page: $page }) {
            hasNextPage
            mangas {
              id
              title
              thumbnailUrl
            }
          }
        }
        """
        vars = {
            "source": source_id,
            "query": query,
            "type": "SEARCH" if query else "POPULAR",
            "page": max(1, int(page)),
        }
        data = self._query(q, vars)
        fsm = data.get("fetchSourceManga") or {}
        return {
            "mangas": fsm.get("mangas", []),
            "hasNextPage": bool(fsm.get("hasNextPage")),
        }

    _MAX_PAGE = 100000  # garde-fou anti-boucle infinie

    def find_last_page(self, source_id: str, query: str = "") -> int:
        """Trouve le numéro de la dernière page (recherche exponentielle puis
        binaire sur `hasNextPage`). Les jeux de résultats Suwayomi n'exposent pas
        de total ; on le déduit en ~O(log N) requêtes (rapides car la source
        pagine en mémoire). La source clampe les pages au-delà de la fin, donc la
        1re page avec `hasNextPage=False` EST la dernière page réelle."""
        # Exponentiel : 1, 2, 4, 8, … jusqu'à une page sans page suivante.
        lo, hi = 1, 1
        while self.search_manga(source_id, query, hi).get("hasNextPage"):
            lo = hi
            hi *= 2
            if hi >= self._MAX_PAGE:
                return self._MAX_PAGE
        # Binaire : plus petite page (lo, hi] avec hasNextPage=False.
        while lo + 1 < hi:
            mid = (lo + hi) // 2
            if self.search_manga(source_id, query, mid).get("hasNextPage"):
                lo = mid
            else:
                hi = mid
        return hi

    @staticmethod
    def _title_initial(title: str) -> str:
        """Initiale normalisée d'un titre pour le tri alphabétique. Les titres qui
        ne commencent pas par une lettre (#, chiffres…) trient AVANT 'A'."""
        t = (title or "").strip().upper()
        c = t[0] if t else "#"
        return c if c.isalpha() else "#"  # '#' (ASCII 35) < 'A' (65)

    def find_page_for_letter(
        self, source_id: str, query: str, letter: str, last_page: int
    ) -> int:
        """Page où commence une lettre donnée, par recherche binaire sur l'initiale
        du 1er titre de chaque page (le catalogue Suwayomi est trié alphabétiquement
        pour la plupart des sources). '#' -> page 1."""
        letter = (letter or "").strip().upper()
        if not letter or letter == "#" or not letter.isalpha():
            return 1
        lo, hi = 1, max(1, int(last_page))
        while lo < hi:
            mid = (lo + hi) // 2
            mangas = self.search_manga(source_id, query, mid).get("mangas") or []
            initial = self._title_initial(mangas[0]["title"]) if mangas else "Z"
            if initial < letter:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def get_manga_details(self, suwayomi_manga_id: str) -> Dict[str, Any]:
        q = """
        query GetManga($id: Int!) {
          manga(id: $id) {
            id
            title
            description
            thumbnailUrl
            author
            artist
            status
          }
        }
        """
        vars = {"id": int(suwayomi_manga_id)}
        data = self._query(q, vars)
        return data.get("manga", {}) or {}

    def fetch_manga_details(self, suwayomi_manga_id: str) -> Dict[str, Any]:
        """Détails COMPLETS depuis la source (description, auteur, genres, statut).

        `manga(id:)` ne renvoie que les données minimales du listing (titre +
        vignette) ; la description n'est peuplée qu'après un fetch source. La
        mutation `fetchManga` déclenche ce fetch et renvoie la fiche complète."""
        q = """
        mutation FetchManga($id: Int!) {
          fetchManga(input: { id: $id }) {
            manga {
              id
              title
              description
              thumbnailUrl
              author
              artist
              status
              genre
              realUrl
            }
          }
        }
        """
        data = self._query(q, {"id": int(suwayomi_manga_id)})
        manga = (data.get("fetchManga") or {}).get("manga") or {}
        if not manga:
            # Repli : au moins les données en cache si le fetch source a échoué.
            manga = self.get_manga_details(suwayomi_manga_id)
        return manga

    def get_chapters(self, suwayomi_manga_id: str) -> List[Dict[str, Any]]:
        # Suwayomi v2.x : `manga.chapters` est un ChapterNodeList (connection),
        # donc il faut passer par `nodes` — sinon "Field 'id' in type
        # 'ChapterNodeList' is undefined" -> la requête échoue et on re-scrape la
        # source à chaque ouverture (lent). On lit d'abord le cache via `nodes`.
        q = """
        query GetChapters($id: Int!) {
          manga(id: $id) {
            chapters {
              nodes {
                id
                name
                chapterNumber
              }
            }
          }
        }
        """
        vars = {"id": int(suwayomi_manga_id)}
        data = self._query(q, vars)
        manga = data.get("manga") or {}
        chapters = (manga.get("chapters") or {}).get("nodes") or []
        if not chapters:
            mut = """
            mutation FetchChapters($id: Int!) {
              fetchChapters(input: { mangaId: $id }) {
                chapters {
                  id
                  name
                  chapterNumber
                }
              }
            }
            """
            data_mut = self._query(mut, {"id": int(suwayomi_manga_id)})
            chapters = data_mut.get("fetchChapters", {}).get("chapters", [])
        return chapters

    def get_pages(self, suwayomi_chapter_id: str) -> List[str]:
        mut = """
        mutation FetchPages($id: Int!) {
          fetchChapterPages(input: { id: $id }) {
            chapter {
              id
              pages
            }
          }
        }
        """
        data = self._query(mut, {"id": int(suwayomi_chapter_id)})
        pages = (
            data.get("fetchChapterPages", {}).get("chapter", {}).get("pages", [])
            if data.get("fetchChapterPages")
            else []
        )
        if not pages:
            q = """
            query GetPages($id: Int!) {
              chapter(id: $id) {
                pages
              }
            }
            """
            data_q = self._query(q, {"id": int(suwayomi_chapter_id)})
            pages = (
                data_q.get("chapter", {}).get("pages", [])
                if data_q.get("chapter")
                else []
            )
        return pages

    def get_extensions(self) -> List[Dict[str, Any]]:
        q = """
        query {
          extensions {
            nodes {
              pkgName
              name
              versionName
              isInstalled
              hasUpdate
              lang
              iconUrl
              isNsfw
              isObsolete
            }
          }
        }
        """
        data = self._query(q)
        return data.get("extensions", {}).get("nodes", [])

    def update_extensions(self, ids: List[str], action: str) -> List[Dict[str, Any]]:
        mut = """
        mutation UpdateExtensions($ids: [String!]!, $patch: UpdateExtensionPatchInput!) {
          updateExtensions(input: { ids: $ids, patch: $patch }) {
            extensions {
              pkgName
              name
              isInstalled
              hasUpdate
            }
          }
        }
        """
        patch = {}
        if action == "install":
            patch["install"] = True
        elif action == "uninstall":
            patch["uninstall"] = True
        elif action == "update":
            patch["update"] = True
        else:
            raise ValueError(f"Invalid action: {action}")

        vars = {"ids": ids, "patch": patch}
        data = self._query(mut, vars)
        return data.get("updateExtensions", {}).get("extensions", [])
