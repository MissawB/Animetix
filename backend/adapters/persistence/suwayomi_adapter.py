import logging
from typing import Any, Dict, List, Optional

import httpx
from core.config import settings
from core.ports.suwayomi_port import SuwayomiPort

logger = logging.getLogger("animetix.suwayomi")


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

    def search_manga(self, source_id: str, query: str = "") -> List[Dict[str, Any]]:
        q = """
        query Search($source: LongString!, $query: String, $type: SourceMangaType!) {
          fetchSourceManga(source: $source, query: $query, type: $type, page: 1) {
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
        }
        data = self._query(q, vars)
        return data.get("fetchSourceManga", {}).get("mangas", [])

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

    def get_chapters(self, suwayomi_manga_id: str) -> List[Dict[str, Any]]:
        q = """
        query GetChapters($id: Int!) {
          manga(id: $id) {
            chapters {
              id
              name
              chapterNumber
            }
          }
        }
        """
        vars = {"id": int(suwayomi_manga_id)}
        data = self._query(q, vars)
        chapters = (
            data.get("manga", {}).get("chapters", []) if data.get("manga") else []
        )
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
