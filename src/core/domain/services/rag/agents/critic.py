import logging
from typing import Dict
from core.domain.entities.ai_schemas import CritiqueResult
from core.domain.services.llm_service import LLMService
from core.domain.services.prompt_manager import PromptManager

logger = logging.getLogger("animetix.rag.critic")

class ResponseCritic:
    """Agent responsable de l'évaluation de la pertinence du contexte récupéré."""
    def __init__(self, llm_service: LLMService, prompt_manager: PromptManager):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager

    def evaluate(self, query: str, context: str, thinking_budget: int = 0, thinking_mode: bool = False) -> CritiqueResult:
        crit_prompt, crit_sys = self.prompt_manager.get_prompt("critic_evaluation", query=query, context=context)
        crit_raw = self.llm_service.generate(
            crit_prompt, 
            crit_sys, 
            use_slm=True, 
            thinking_budget=thinking_budget,
            thinking_mode=thinking_mode
        )
        
        try:
            import orjson
            if '{' in crit_raw and '}' in crit_raw:
                data = orjson.loads(crit_raw[crit_raw.find('{'):crit_raw.rfind('}')+1])
                return CritiqueResult(**data)
        except Exception as e:
            logger.warning(f"Critique parsing failed: {e}. Defaulting to PROCEED.")
            
        return CritiqueResult(is_relevant=True, relevance_score=1.0, suggested_action="PROCEED")
