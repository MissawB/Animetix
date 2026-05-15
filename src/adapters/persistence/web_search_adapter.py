import requests
from typing import List, Dict
from core.ports.web_search_port import WebSearchPort

class DuckDuckGoSearchAdapter(WebSearchPort):
    """
    Adaptateur pour la recherche Web via DuckDuckGo (API libre/HTML parsing).
    Sert de source d'information temps réel pour l'Agentic RAG.
    """
    def __init__(self):
        self.api_url = "https://api.duckduckgo.com"

    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Simulation d'une recherche DuckDuckGo."""
        print(f"🌐 Web Searching for: '{query}'...")
        # Note: In a real implementation, we would use a search API like Serper, Tavily or DDG scraping.
        # Here we mock the behavior for the prototype.
        return [
            {
                "title": f"Result for {query}",
                "url": "https://example.com/anime-info",
                "snippet": f"Dernières actualités sur {query} : les fans attendent la saison 2 avec impatience."
            }
        ]

    def get_content(self, url: str) -> str:
        """Récupère le texte brut d'une page."""
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                return res.text[:2000] # Limite pour le contexte LLM
        except: pass
        return ""
