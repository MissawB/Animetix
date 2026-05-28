import logging
import json
import re
from typing import Dict, Optional
from core.domain.exceptions import InferenceError, InfrastructureError
from core.domain.entities.ai_schemas import (
    JudgeEvaluation, JudgeAction, DebateOutcome
)
from core.domain.services.llm_service import LLMService
from core.domain.services.prompt_manager import PromptManager

logger = logging.getLogger("animetix.rag.debate_manager")

def robust_json_loads(raw: str) -> dict:
    clean_raw = raw.strip()
    if "```" in clean_raw:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_raw, re.DOTALL | re.IGNORECASE)
        if match:
            clean_raw = match.group(1)
            
    first_curly = clean_raw.find('{')
    last_curly = clean_raw.rfind('}')
    if first_curly != -1 and last_curly != -1:
        json_str = clean_raw[first_curly:last_curly+1]
    else:
        json_str = clean_raw
        
    try:
        return json.loads(json_str)
    except Exception as e:
        logger.debug(f"Initial JSON parse failed: {e}. Attempting recovery...")
        
    try:
        # Basic cleaning
        json_str = re.sub(r'//.*?\n', '\n', json_str)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
        json_str = re.sub(r'[\x00-\x1F\x7F]', '', json_str)
        return json.loads(json_str)
    except Exception as e:
        try:
            import orjson
            return orjson.loads(json_str)
        except Exception:
            raise ValueError(f"Failed to parse JSON: {e}")

def sanitize_judge_data(data: dict) -> dict:
    # 1. next_action mapping
    action_val = str(data.get("next_action", "")).upper().strip()
    if "APPROVE" in action_val or action_val in ["YES", "OK", "PASS"]:
        data["next_action"] = JudgeAction.APPROVE
    elif "REPLAN" in action_val:
        data["next_action"] = JudgeAction.REPLAN
    elif "RESEARCH" in action_val:
        data["next_action"] = JudgeAction.RESEARCH_MORE
    elif "REWRITE" in action_val:
        data["next_action"] = JudgeAction.REWRITE
    else:
        try:
            data["next_action"] = JudgeAction(action_val)
        except ValueError:
            data["next_action"] = JudgeAction.REWRITE
            
    # 2. faithfulness_score
    try:
        data["faithfulness_score"] = float(data.get("faithfulness_score", 1.0))
        data["faithfulness_score"] = max(0.0, min(1.0, data["faithfulness_score"]))
    except (ValueError, TypeError):
        data["faithfulness_score"] = 1.0
        
    # 3. relevancy_score
    try:
        data["relevancy_score"] = float(data.get("relevancy_score", 1.0))
        data["relevancy_score"] = max(0.0, min(1.0, data["relevancy_score"]))
    except (ValueError, TypeError):
        data["relevancy_score"] = 1.0
        
    # 4. hallucination_detected
    h_detected = data.get("hallucination_detected")
    if isinstance(h_detected, str):
        data["hallucination_detected"] = h_detected.lower() == "true"
    elif h_detected is None:
        data["hallucination_detected"] = False
        
    # 5. reasoning
    if "reasoning" not in data or not data["reasoning"]:
        data["reasoning"] = "No reasoning provided by the judge."
        
    # 6. is_reliable
    is_rel = data.get("is_reliable")
    if isinstance(is_rel, str):
        data["is_reliable"] = is_rel.lower() == "true"
    elif is_rel is None:
        data["is_reliable"] = not data["hallucination_detected"]
        
    return data

class DebateManager:
    """
    Coordinates specialized judges to evaluate RAG responses and decide on the next action.
    Uses pessimistic consensus: any judge suggesting a non-APPROVE action triggers it.
    """
    def __init__(self, llm_service: LLMService, prompt_manager: PromptManager):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager

    def conduct_debate(self, query: str, context: str, answer: str, thinking_budget: int = 0, thinking_mode: bool = False) -> DebateOutcome:
        critiques: Dict[str, JudgeEvaluation] = {}
        judges = ["judge_lore_expert", "judge_logic_auditor", "judge_critic"]
        
        from concurrent.futures import ThreadPoolExecutor
        
        def run_single_judge(j_key: str):
            try:
                # get_prompt usually returns (prompt, system_prompt)
                prompt, sys = self.prompt_manager.get_prompt(j_key, query=query, context=context, answer=answer)
                
                # Split budget among judges if thinking_mode is enabled
                current_budget = thinking_budget // len(judges) if thinking_mode else 0
                
                raw = self.llm_service.generate(
                    prompt, 
                    sys, 
                    use_slm=True,
                    thinking_budget=current_budget,
                    thinking_mode=thinking_mode
                )
                
                try:
                    data = robust_json_loads(raw)
                    sanitized_data = sanitize_judge_data(data)
                    return j_key, JudgeEvaluation(**sanitized_data)
                except Exception as parse_err:
                    logger.warning(f"Judge {j_key} response parsed with errors: {parse_err}. Raw response: {raw}")
                    return j_key, None
            except (InferenceError, InfrastructureError) as e:
                logger.error(f"DebateManager inference/infrastructure error: {e}")
                return j_key, None
            except Exception as e:
                logger.error(f"Unexpected error in DebateManager: {e}", exc_info=True)
                return j_key, None

        # Exécuter les 3 juges en parallèle dans des threads distincts
        with ThreadPoolExecutor(max_workers=len(judges)) as executor:
            results = list(executor.map(run_single_judge, judges))
            
        for res in results:
            if res and res[1] is not None:
                critiques[res[0]] = res[1]

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
