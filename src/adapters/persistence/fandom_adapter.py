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
            "action": "parse",
            "page": character_name,
            "format": "json",
            "prop": "wikitext"
        }
        try:
            logger.info(f"Fetching Fandom data for character: {character_name}")
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if "error" in data:
                logger.error(f"Fandom API Error: {data['error']['info']}")
                raise Exception(f"Fandom API Error: {data['error']['info']}")
                
            wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
            
            return {
                "name": character_name,
                "wikitext": wikitext
            }
        except requests.RequestException as e:
            logger.error(f"Failed to fetch data from Fandom: {e}")
            raise
