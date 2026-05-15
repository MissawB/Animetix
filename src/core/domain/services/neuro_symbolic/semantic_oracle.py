import orjson
import logging
from typing import Dict, List, Optional
from core.ports.inference_port import InferencePort


logger = logging.getLogger('animetix.neuro_symbolic.oracle')

class SemanticOracle:
    """
    Oracle sémantique utilisant un LLM.
    Responsable de l'extraction des faits et de la vulgarisation des preuves.
    """
    def __init__(self, inference_engine: InferencePort):
        self.inference_engine = inference_engine

    def extract_properties(self, media_type: str, items: List[str]) -> Dict[str, Dict[str, bool]]:
        """Extrait des propriétés booléennes pour une liste d'items."""
        items_str = ", ".join([f"'{i}'" for i in items])
        prompt = f"""
        Analyse ces {len(items)} {media_type} : {items_str}.
        Propose 3 propriétés binaires (vrai/faux) qui permettent de les distinguer logiquement.
        Par exemple : 'est_un_film', 'possede_des_pouvoirs', 'est_sorti_apres_2010'.
        
        FORMAT JSON STRICT :
        {{
            "{items[0]}": {{"prop1": true, "prop2": false, "prop3": true}},
            ...
        }}
        """
        res = self.inference_engine.generate(prompt, system_prompt="Tu es un expert en ontologie logique. Réponds UNIQUEMENT en JSON.")
        
        try:
            if '{' in res and '}' in res:
                clean_json = res[res.find('{'):res.rfind('}')+1]
                return orjson.loads(clean_json)
        except Exception as e:
            logger.error(f"Oracle Property Extraction Error: {e}")
        return {}

    def explain_proof(self, intruder: str, proof: str) -> str:
        """Traduit une preuve mathématique en explication naturelle."""
        prompt = f"""
        Le solveur logique a identifié l'intrus : '{intruder}'.
        Détails techniques de la preuve : {proof}
        
        Explique de manière simple et narrative à l'utilisateur pourquoi '{intruder}' est l'intrus, 
        en te basant sur les faits logiques identifiés.
        """
        return self.inference_engine.generate(prompt, system_prompt="Tu es un vulgarisateur scientifique pédagogue.")
