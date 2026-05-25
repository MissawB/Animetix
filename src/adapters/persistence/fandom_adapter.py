import requests
import logging
import re
from typing import List, Dict, Any, Optional
from core.ports.fandom_port import FandomPort

logger = logging.getLogger("animetix.fandom")

class FandomAdapter(FandomPort):
    """
    Robust Fandom adapter using search-then-fetch strategy.
    """
    def __init__(self):
        self.api_url = "https://vsbattles.fandom.com/api.php"
        self.base_url = "https://vsbattles.fandom.com"

    def fetch_character_data(self, character_name: str, franchise: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Uses a robust search-then-fetch strategy to retrieve all character variations.
        """
        query = f"{character_name} {franchise} VS Battles Wiki" if franchise else f"{character_name} profile VS Battles Wiki"
        logger.info(f"🔍 [Fandom] Searching for: {query}")

        # 1. Search for all relevant pages
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": 5, # Fetch multiple candidates
            "format": "json"
        }
        
        try:
            res = requests.get(self.api_url, params=search_params, timeout=10)
            res.raise_for_status()
            search_data = res.json()
            
            search_results = search_data.get("query", {}).get("search", [])
            if not search_results:
                logger.warning(f"⚠️ [Fandom] No search results for: {character_name}")
                return []
            
            all_versions = []
            for result in search_results:
                page_title = result["title"]
                logger.info(f"🎯 [Fandom] Found candidate: {page_title}")
                
                # 2. Fetch page content and images for each
                fetch_params = {
                    "action": "query",
                    "titles": page_title,
                    "prop": "pageimages|revisions",
                    "piprop": "original",
                    "rvprop": "content",
                    "format": "json",
                    "formatversion": 2
                }
                
                res = requests.get(self.api_url, params=fetch_params, timeout=10)
                res.raise_for_status()
                data = res.json()
                
                pages = data.get("query", {}).get("pages", [])
                if pages:
                    page = pages[0]
                    all_versions.append({
                        "name": page_title,
                        "wikitext": page.get("revisions", [{}])[0].get("content", ""),
                        "image_url": page.get("original", {}).get("source"),
                        "url": f"{self.base_url}/wiki/{page_title.replace(' ', '_')}"
                    })
            
            return all_versions
            
        except Exception as e:
            logger.error(f"❌ [Fandom] Failed to fetch: {e}")
            return []
