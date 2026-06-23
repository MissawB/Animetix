import logging
import os
from typing import Dict, List

from core.ports.web_search_port import WebSearchPort
from core.utils.gemini_models import GEMINI_FLASH
from core.utils.security import is_safe_url, safe_http_request

logger = logging.getLogger("animetix.persistence.web_search")


class UnifiedWebSearchAdapter(WebSearchPort):
    """
    Unified Web Search Adapter that acts as a real-time information retriever for Agentic RAG.
    Supports Tavily Search API and Google Search Grounding (Gemini).
    """

    def __init__(self):
        # Read API keys from environment
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Routes the search query to the best available search engine:
        1. Tavily Search API (if TAVILY_API_KEY is present)
        2. Gemini Search Grounding (if GEMINI_API_KEY is present)
        """
        if self.tavily_api_key:
            results = self._search_tavily(query, limit)
            if results:
                logger.info(
                    f"🚀 [Tavily] Search successful for: '{query}' ({len(results)} results)"
                )
                return results

        if self.gemini_api_key:
            results = self._search_gemini_grounding(query, limit)
            if results:
                logger.info(
                    f"🚀 [Gemini Grounding] Search successful for: '{query}' ({len(results)} results)"
                )
                return results

        logger.warning(
            f"⚠️ [WebSearch] No active search credentials found for: '{query}'"
        )
        return []

    def _search_tavily(self, query: str, limit: int = 5) -> List[Dict]:
        """Performs search using Tavily API."""
        try:
            url = "https://api.tavily.com/search"
            payload = {
                "api_key": self.tavily_api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": limit,
            }
            # We use safe_http_request to ensure SSRF/redirection protections
            response = safe_http_request("POST", url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                mapped_results = []
                for r in data.get("results", []):
                    url_val = r.get("url", "")
                    if is_safe_url(url_val):
                        mapped_results.append(
                            {
                                "title": r.get("title", ""),
                                "url": url_val,
                                "snippet": r.get("content", ""),
                            }
                        )
                return mapped_results
        except Exception as e:
            logger.error(f"❌ Error during Tavily search: {e}")
        return []

    def _search_gemini_grounding(self, query: str, limit: int = 5) -> List[Dict]:
        """Performs search using Google Search Grounding with Gemini GenAI SDK."""
        try:
            from google import genai  # noqa: E402
            from google.genai import types  # noqa: E402

            client = genai.Client(api_key=self.gemini_api_key)
            prompt = f"Perform a search on: '{query}' and return relevant information."

            response = client.models.generate_content(
                model=GEMINI_FLASH,
                contents=prompt,
                config=types.GenerateContentConfig(tools=[{"google_search": {}}]),
            )

            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if (
                    hasattr(candidate, "grounding_metadata")
                    and candidate.grounding_metadata
                ):
                    metadata = candidate.grounding_metadata
                    chunks = getattr(metadata, "grounding_chunks", [])
                    mapped_results = []
                    for chunk in chunks[:limit]:
                        web = getattr(chunk, "web", None)
                        if web:
                            title = getattr(web, "title", "")
                            uri = getattr(web, "uri", "")
                            if is_safe_url(uri):
                                mapped_results.append(
                                    {
                                        "title": title,
                                        "url": uri,
                                        "snippet": (
                                            response.text[:200]
                                            if hasattr(response, "text")
                                            else ""
                                        ),
                                    }
                                )
                    return mapped_results
        except Exception as e:
            logger.error(f"❌ Error during Gemini Grounding search: {e}")
        return []

    def get_content(self, url: str) -> str:
        """Récupère le texte brut d'une page (SSRF protected with manual redirect validation)."""
        try:
            res = safe_http_request("GET", url, timeout=10)
            if res.status_code == 200:
                return res.text[:2000]  # Limite pour le contexte LLM
        except Exception as e:
            logger.error(f"Failed to fetch content from {url}: {e}")
        return ""
