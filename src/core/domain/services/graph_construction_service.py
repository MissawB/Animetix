import orjson
import logging
from typing import Dict, List
from ...ports.inference_port import InferencePort

logger = logging.getLogger("animetix.graph")

class KnowledgeGraphConstructionService:
    def __init__(self, inference_engine: InferencePort):
        self.inference_engine = inference_engine

    def extract_entities_and_relations(self, title: str, description: str, media_type: str) -> Dict:
        """
        Utilise le LLM pour extraire des entités et des relations structurées à partir d'un synopsis.
        """
        prompt = f"""
        MISSION : Analyse le synopsis suivant et extrais les entités clés et leurs relations pour un graphe de connaissances.
        
        TITRE : {title}
        TYPE : {media_type}
        SYNOPSIS : {description}
        
        FORMAT DE SORTIE ATTENDU (JSON UNIQUEMENT) :
        {{
          "entities": [
            {{"name": "Nom", "type": "Person|Organization|Location|Concept", "description": "bref"}}
          ],
          "relations": [
            {{"source": "Entité A", "target": "Entité B", "type": "LOVES|ENEMY_OF|MEMBER_OF|LOCATED_IN|PART_OF"}}
          ]
        }}
        
        CONSIGNE : Ne cite que les éléments majeurs. Reste fidèle au texte.
        """
        
        system_prompt = "Tu es un expert en ingénierie de la connaissance et en ontologies d'anime/manga."
        
        response = self.inference_engine.generate(prompt, system_prompt)
        
        try:
            # Nettoyage de la réponse au cas où le LLM ajoute du texte autour du JSON
            if '{' in response and '}' in response:
                clean_json = response[response.find('{'):response.rfind('}')+1]
                return orjson.loads(clean_json)
        except Exception as e:
            logger.error(f"Graph Extraction Error: {e}")
            
        return {"entities": [], "relations": []}
