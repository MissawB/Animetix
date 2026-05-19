import logging
from typing import Dict, Optional
from core.domain.entities.ai_schemas import (
    JudgeEvaluation, JudgeAction, DebateOutcome
)
from core.domain.services.llm_service import LLMService
from core.domain.services.prompt_manager import PromptManager

logger = logging.getLogger("animetix.rag.debate_manager")

class DebateManager:
    """
    Coordinates specialized judges to evaluate RAG responses and decide on the next action.
    Uses pessimistic consensus: any judge suggesting a non-APPROVE action triggers it.
    """
    def __init__(self, llm_service: LLMService, prompt_manager: PromptManager):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager

    def conduct_debate(self, query: str, context: str, answer: str) -> DebateOutcome:
        critiques: Dict[str, JudgeEvaluation] = {}
        judges = ["judge_lore_expert", "judge_logic_auditor", "judge_critic"]
        
        for j_key in judges:
            try:
                # get_prompt usually returns (prompt, system_prompt)
                prompt, sys = self.prompt_manager.get_prompt(j_key, query=query, context=context, answer=answer)
                raw = self.llm_service.generate(prompt, sys, use_slm=True)
                
                import orjson
                if '{' in raw and '}' in raw:
                    data = orjson.loads(raw[raw.find('{'):raw.rfind('}')+1])
                    critiques[j_key] = JudgeEvaluation(**data)
                else:
                    logger.warning(f"Judge {j_key} returned non-JSON response: {raw}")
            except Exception as e:
                logger.error(f"Failed to execute or parse {j_key} response: {e}")

        # If no critiques were successfully parsed, we can't make a decision.
        # Fallback to REWRITE if critical failure, or APPROVE if we want to be permissive (but plan says pessimistic).
        if not critiques:
            return DebateOutcome(
                critiques={},
                consensus_action=JudgeAction.REWRITE,
                final_reasoning="Debate failed: No valid critiques received. Defaulting to REWRITE for safety."
            )

        # Consensus Logic (Pessimistic)
        # Priority: REPLAN > RESEARCH_MORE > REWRITE > APPROVE
        actions = [c.next_action for c in critiques.values()]
        
        if JudgeAction.REPLAN in actions:
            consensus = JudgeAction.REPLAN
        elif JudgeAction.RESEARCH_MORE in actions:
            consensus = JudgeAction.RESEARCH_MORE
        elif JudgeAction.REWRITE in actions:
            consensus = JudgeAction.REWRITE
        else:
            consensus = JudgeAction.APPROVE
            
        final_reasoning_parts = [f"[{k}]: {v.reasoning}" for k, v in critiques.items()]
        final_reasoning = "\n".join(final_reasoning_parts)
        
        return DebateOutcome(
            critiques=critiques,
            consensus_action=consensus,
            final_reasoning=f"Debate Consensus: {consensus}. \nDetails:\n{final_reasoning}"
        )
