import json
import logging
import httpx
from typing import Dict, Any, Optional
from core.domain.services.llm_service import LLMService
from core.domain.services.prompt_manager import PromptManager
from core.ports.web_search_port import WebSearchPort

logger = logging.getLogger("animetix.rag.librarian")

from core.utils.security import safe_http_request
from urllib.parse import quote

class LibrarianAgent:
    """
    Agent responsable de l'identification des lacunes de connaissances
    et de la récupération de données externes (Jikan, Web).
    """
    def __init__(self, llm_service: LLMService, prompt_manager: PromptManager, web_search: WebSearchPort):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager
        self.web_search = web_search

    def identify_gap(self, query: str, context: str) -> Optional[Dict[str, Any]]:
        """
        Analyse la requête et le contexte actuel pour identifier si une information manque.
        """
        logger.info("🕵️ Librarian: Identifying knowledge gaps...")
        
        try:
            prompt, system = self.prompt_manager.get_prompt("librarian_mission", query=query, context=context)
            
            # Utilisation du SLM pour l'analyse des lacunes (plus rapide et suffisant)
            response = self.llm_service.generate(prompt, system, use_slm=True)
            
            if not response:
                return None
            
            # Tentative d'extraction du JSON de la réponse
            # Parfois le LLM peut inclure du texte explicatif autour du JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                try:
                    gap_data = json.loads(json_str)
                    
                    # Vérification des champs requis selon le schéma attendu
                    if "source_type" in gap_data:
                        # Si source_type est NONE, il n'y a pas de lacune à combler
                        if gap_data["source_type"].upper() == "NONE":
                            logger.info("✅ Librarian: No knowledge gap identified.")
                            return None
                        
                        logger.info(f"📍 Librarian: Gap identified! Source: {gap_data.get('source_type')}")
                        return gap_data
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Librarian: Failed to parse JSON from response: {response}")
            
            return None
        except Exception as e:
            logger.error(f"❌ Librarian gap identification failed: {e}")
            return None

    def fetch_data(self, gap_json: Dict[str, Any]) -> str:
        """
        Récupère les données manquantes via la source appropriée (Jikan ou Web).
        """
        source_type = gap_json.get("source_type", "").upper()
        query = gap_json.get("query", "")
        
        if not query:
            return "No query provided for retrieval."
            
        logger.info(f"📚 Librarian: Fetching data from {source_type} for: {query}")
        
        if source_type == "JIKAN":
            return self._fetch_from_jikan(query)
        elif source_type == "WEB":
            return self._fetch_from_web(query)
        else:
            return f"Unsupported source type: {source_type}"

    def _fetch_from_jikan(self, query: str) -> str:
        """
        Appelle l'API Jikan (V4) pour obtenir des informations sur les anime.
        """
        try:
            # Encodage strict du paramètre de recherche
            safe_query = quote(query)
            url = f"https://api.jikan.moe/v4/anime?q={safe_query}&limit=3"
            
            # Utilisation de safe_http_request pour validation SSRF des redirections
            response = safe_http_request("GET", url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            items = data.get("data", [])
            
            if not items:
                return f"No results found on Jikan for '{query}'"
                
            results_text = "--- RÉSULTATS JIKAN (Anime) ---\n"
            for item in items:
                title = item.get("title")
                status = item.get("status")
                episodes = item.get("episodes", "?")
                score = item.get("score", "?")
                synopsis = item.get("synopsis", "Pas de synopsis.")
                
                results_text += f"Titre: {title}\nStatut: {status} ({episodes} eps)\nScore: {score}/10\nSynopsis: {synopsis[:500]}...\n\n"
            
            return results_text
        except Exception as e:
            logger.error(f"❌ Librarian: Jikan fetch error: {e}")
            return f"Error fetching from Jikan: {str(e)}"

    def _fetch_from_web(self, query: str) -> str:
        """
        Utilise le port de recherche Web pour trouver des informations récentes.
        """
        try:
            search_results = self.web_search.search(query, limit=5)
            
            if not search_results:
                return f"No web search results found for '{query}'"
                
            results_text = "--- RÉSULTATS RECHERCHE WEB ---\n"
            for res in search_results:
                title = res.get("title", "Sans titre")
                snippet = res.get("snippet", res.get("content", ""))
                url = res.get("url", "")
                
                results_text += f"Source: {title}\nSnippet: {snippet}\nURL: {url}\n\n"
            
            return results_text
        except Exception as e:
            logger.error(f"❌ Librarian: Web search error: {e}")
            return f"Error fetching from Web: {str(e)}"
