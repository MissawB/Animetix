import requests
import logging
from typing import Dict, Any
from core.ports.fandom_port import FandomPort

logger = logging.getLogger("animetix.fandom")

class FandomAdapter(FandomPort):
    """
    Adapter for fetching character data from VS Battles Wiki (Fandom).
    Uses the MediaWiki API.
    """
    def __init__(self):
        self.api_url = "https://vsbattles.fandom.com/api.php"

    def fetch_character_data(self, character_name: str) -> Dict[str, Any]:
        params = {
            "action": "query",
            "titles": character_name,
            "prop": "pageimages|revisions",
            "piprop": "original",
            "rvprop": "content",
            "format": "json",
            "formatversion": 2,
            "redirects": 1
        }
        try:
            logger.info(f"Fetching Fandom data for character: {character_name}")
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            pages = data.get("query", {}).get("pages", [])
            
            if not pages or pages[0].get("missing"):
                logger.warning(f"Character not found: {character_name}")
                return {"name": character_name, "wikitext": "", "image_url": None}
                
            page = pages[0]
            wikitext = page.get("revisions", [{}])[0].get("content", "")
            image_url = page.get("original", {}).get("source")
            
            return {
                "name": character_name,
                "wikitext": wikitext,
                "image_url": image_url
            }
        except Exception as e:
            logger.error(f"Failed to fetch data from Fandom: {e}")
            raise
