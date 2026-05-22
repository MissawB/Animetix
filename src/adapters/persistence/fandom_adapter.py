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

    def fetch_character_data(self, character_name: str, franchise: Optional[str] = None) -> Dict[str, Any]:
        """
        Uses a robust search-then-fetch strategy with multiple name variations.
        """
        # Generate name variations for searching
        names_to_try = [character_name]
        if " " in character_name:
            parts = character_name.split(" ")
            names_to_try.append(parts[0]) # First name
            names_to_try.append(parts[-1]) # Last name
            
        for name_variation in names_to_try:
            query = f"{name_variation} {franchise} VS Battles Wiki" if franchise else f"{name_variation} profile VS Battles Wiki"
            logger.info(f"🔍 [Fandom] Trying search: {query}")

            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": 1,
                "format": "json"
            }
            
            try:
                res = requests.get(self.api_url, params=search_params, timeout=10)
                res.raise_for_status()
                search_data = res.json()
                search_results = search_data.get("query", {}).get("search", [])
                
                if search_results:
                    page_title = search_results[0]["title"]
                    logger.info(f"🎯 [Fandom] Found match: {page_title}")
                    
                    # Fetch page content
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
                        return {
                            "name": page_title,
                            "wikitext": page.get("revisions", [{}])[0].get("content", ""),
                            "image_url": page.get("original", {}).get("source"),
                            "url": f"{self.base_url}/wiki/{page_title.replace(' ', '_')}"
                        }
            except Exception as e:
                logger.warning(f"⚠️ [Fandom] Search attempt failed for {name_variation}: {e}")
                continue

        logger.warning(f"⚠️ [Fandom] No search results for any variation of: {character_name}")
        return {"name": character_name, "wikitext": "", "image_url": None}
