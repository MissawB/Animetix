import httpx
import logging
from typing import List, Dict
from core.ports.web_search_port import WebSearchPort
from core.utils.security import is_safe_url
from ddgs import DDGS

logger = logging.getLogger("animetix.web")

class DuckDuckGoSearchAdapter(WebSearchPort):
    """
    Adaptateur pour la recherche Web via DuckDuckGo (API libre/HTML parsing).
    Sert de source d'information temps réel pour l'Agentic RAG.
    """
    def __init__(self):
        self.api_url = "https://api.duckduckgo.com"

    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Recherche DuckDuckGo via DDGS."""
        logger.info(f"🌐 Web Searching for: '{query}'...")
        try:
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=limit)
                if not results:
                    return []
                
                mapped_results = []
                for r in results:
                    url = r.get("href", "")
                    # Sécurité: Ne pas retourner d'URLs non-sûres dans les résultats de recherche
                    if is_safe_url(url):
                        mapped_results.append({
                            "title": r.get("title", ""),
                            "url": url,
                            "snippet": r.get("body", "")
                        })
                return mapped_results
        except Exception as e:
            logger.error(f"Error during DuckDuckGo search for '{query}': {e}")
            return []

    def get_content(self, url: str) -> str:
        """Récupère le texte brut d'une page (SSRF protected)."""
        if not is_safe_url(url):
            logger.warning(f"Blocked content fetching from unsafe URL: {url}")
            return ""
            
        try:
            res = httpx.get(url, timeout=10, follow_redirects=True)
            if res.status_code == 200:
                return res.text[:2000] # Limite pour le contexte LLM
        except Exception as e:
            logger.error(f"Failed to fetch content from {url}: {e}")
        return ""
