import logging
from typing import Dict, Optional
from core.domain.entities.ai_schemas import SearchPlan
from core.domain.services.llm_service import LLMService
from core.domain.services.prompt_manager import PromptManager

logger = logging.getLogger("animetix.rag.planner")

class SearchPlanner:
    """Agent responsable de l'analyse de la requête et de la planification de la recherche."""
    def __init__(self, llm_service: LLMService, prompt_manager: PromptManager):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager

    def plan(self, query: str, memories: str = "", thinking_budget: int = 0, thinking_mode: bool = False) -> SearchPlan:
        plan_prompt, plan_sys = self.prompt_manager.get_prompt("searcher_plan", query=query)
        if memories:
            plan_sys += f"\nContexte utilisateur : {memories}"
            
        plan_raw = self.llm_service.generate(
            plan_prompt, 
            plan_sys, 
            use_slm=True, 
            thinking_budget=thinking_budget,
            thinking_mode=thinking_mode
        )
        
        try:
            import orjson
            if '{' in plan_raw and '}' in plan_raw:
                data = orjson.loads(plan_raw[plan_raw.find('{'):plan_raw.rfind('}')+1])
                return SearchPlan(**data)
        except Exception as e:
            logger.warning(f"Plan parsing failed: {e}. Using fallback.")
            
        return SearchPlan(optimized_query=query, reasoning="Fallback", requires_web=False)
