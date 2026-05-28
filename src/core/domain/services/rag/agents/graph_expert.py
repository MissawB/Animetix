import logging
import orjson
from typing import Dict, Optional
from core.domain.services.llm_service import LLMService
from core.domain.services.prompt_manager import PromptManager
from core.domain.exceptions import InferenceError, InfrastructureError

logger = logging.getLogger("animetix.rag.graph_expert")

class GraphExpert:
    def __init__(self, llm_service: LLMService, prompt_manager: PromptManager):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager

    def generate_cypher(self, query: str, reasoning: str) -> Optional[str]:
        """
        Translates a natural language query and its reasoning into a Cypher query.
        """
        try:
            prompt, sys = self.prompt_manager.get_prompt("graph_expert", query=query, reasoning=reasoning)
            res_raw = self.llm_service.generate(prompt, sys, use_slm=True)
            
            # Extract JSON from potential markdown blocks or noise
            if '{' in res_raw and '}' in res_raw:
                start_idx = res_raw.find('{')
                end_idx = res_raw.rfind('}') + 1
                data = orjson.loads(res_raw[start_idx:end_idx])
                return data.get('cypher')
            
            logger.warning(f"No JSON found in LLM response: {res_raw}")
            return None
        except (InferenceError, InfrastructureError) as e:
            logger.error(f"Graph Expert inference error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in GraphExpert: {e}", exc_info=True)
            return None
