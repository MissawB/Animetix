from backend.core.domain.services.rag.processors.base import StateProcessor
from backend.core.domain.entities.ai_schemas import RAGContext, RAGState, JudgeAction
import logging

logger = logging.getLogger('animetix.rag_workflow')

class JudgeProcessor(StateProcessor):
    def __init__(self, debate_manager, xai_collector=None):
        self.debate_manager = debate_manager
        self.xai_collector = xai_collector

    def process(self, ctx: RAGContext) -> RAGState:
        # Based on RAGWorkflowManager._handle_judge
        outcome = self.debate_manager.conduct_debate(
            ctx.query, 
            ctx.truth_path, 
            ctx.full_answer,
            thinking_budget=ctx.thinking_budget,
            thinking_mode=ctx.thinking_mode
        )
        ctx.debate_outcome = outcome
        if self.xai_collector:
            self.xai_collector.log_agent_thought("ResponseJudge", f"Consensus : {outcome.consensus_action}. Raisonnement : {outcome.final_reasoning}")
            
        action = outcome.consensus_action
        if ctx.iteration >= 10 and action == JudgeAction.REWRITE:
            return RAGState.FINALIZE
        
        if action == JudgeAction.APPROVE:
            return RAGState.FINALIZE
        elif action == JudgeAction.REWRITE:
            ctx.correction_feedback = f"DÉFAUT DÉTECTÉ: {outcome.final_reasoning}. Corrige en restant fidèle au contexte."
            return RAGState.SYNTHESIZE
        elif action == JudgeAction.RESEARCH_MORE:
            if len(ctx.truth_path) < 200 and not ctx.knowledge_acquired:
                return RAGState.ACQUIRE_KNOWLEDGE
            else:
                return RAGState.RESEARCH
        elif action == JudgeAction.REPLAN:
            return RAGState.PLAN
        else:
            return RAGState.FINALIZE
