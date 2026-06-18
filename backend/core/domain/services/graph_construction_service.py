import logging
from typing import Dict

from ...ports.inference_port import InferencePort
from .prompt_manager import PromptManager

logger = logging.getLogger("animetix.graph")


class KnowledgeGraphConstructionService:
    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager

    def extract_entities_and_relations(
        self, title: str, description: str, media_type: str
    ) -> Dict:
        """
        Utilise le LLM pour extraire des entités et des relations structurées à partir d'un synopsis.
        """
        from ..entities.ai_schemas import GraphExtraction  # noqa: E402

        prompt, system_prompt = self.prompt_manager.get_prompt(
            "graph_construction",
            title=title,
            media_type=media_type,
            description=description,
        )

        extraction = self.inference_engine.generate_structured(
            prompt=prompt, response_model=GraphExtraction, system_prompt=system_prompt
        )

        return extraction.model_dump()
