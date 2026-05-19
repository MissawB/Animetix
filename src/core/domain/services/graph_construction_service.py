import orjson
import logging
from typing import Dict, List
from ...ports.inference_port import InferencePort
from .prompt_manager import PromptManager

logger = logging.getLogger("animetix.graph")

class KnowledgeGraphConstructionService:
    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager

    def extract_entities_and_relations(self, title: str, description: str, media_type: str) -> Dict:
        """
        Utilise le LLM pour extraire des entités et des relations structurées à partir d'un synopsis.
        """
        prompt, system_prompt = self.prompt_manager.get_prompt(
            "graph_construction",
            title=title,
            media_type=media_type,
            description=description
        )
        
        response = self.inference_engine.generate(prompt, system_prompt)
        
        try:
            # Nettoyage de la réponse au cas où le LLM ajoute du texte autour du JSON
            if '{' in response and '}' in response:
                clean_json = response[response.find('{'):response.rfind('}')+1]
                return orjson.loads(clean_json)
        except Exception as e:
            logger.error(f"Graph Extraction Error: {e}")
            
        return {"entities": [], "relations": []}
