import orjson
import logging
from typing import Dict, List
from core.ports.inference_port import InferencePort
from core.domain.services.prompt_manager import PromptManager


logger = logging.getLogger("animetix.neuro_symbolic.oracle")


class SemanticOracle:
    """
    Oracle sémantique utilisant un LLM.
    Responsable de l'extraction des faits et de la vulgarisation des preuves.
    """

    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager

    def extract_properties(
        self, media_type: str, items: List[str]
    ) -> Dict[str, Dict[str, bool]]:
        """Extrait des propriétés booléennes pour une liste d'items."""
        items_str = ", ".join([f"'{i}'" for i in items])
        prompt, system = self.prompt_manager.get_prompt(
            "semantic_oracle_reasoning",
            num_items=len(items),
            media_type=media_type,
            items_str=items_str,
            first_item=items[0] if items else "",
        )
        res = self.inference_engine.generate(prompt, system_prompt=system)

        try:
            if "{" in res and "}" in res:
                clean_json = res[res.find("{") : res.rfind("}") + 1]
                return orjson.loads(clean_json)
        except Exception as e:
            logger.error(f"Oracle Property Extraction Error: {e}")
        return {}

    def explain_proof(self, intruder: str, proof: str) -> str:
        """Traduit une preuve mathématique en explication naturelle."""
        prompt, system = self.prompt_manager.get_prompt(
            "semantic_oracle_explanation", intruder=intruder, proof=proof
        )
        return self.inference_engine.generate(prompt, system_prompt=system)
