from backend.core.domain.services.rag.processors.base import StateProcessor
from backend.core.domain.entities.ai_schemas import (
    RAGContext,
    RAGState,
    StreamStep,
    JudgeAction,
)
from typing import Generator
import logging

logger = logging.getLogger("animetix.rag_workflow")


class JudgeProcessor(StateProcessor):
    def __init__(self, debate_manager):
        self.debate_manager = debate_manager

    def process(
        self, ctx: RAGContext, xai_collector=None
    ) -> Generator[dict, None, RAGState]:
        yield StreamStep(
            type="thought", content="[Swarm] Début du débat multi-agents..."
        ).model_dump()
        outcome = self.debate_manager.conduct_debate(
            ctx.query,
            ctx.truth_path,
            ctx.full_answer,
            thinking_budget=ctx.thinking_budget,
            thinking_mode=ctx.thinking_mode,
            xai_collector=xai_collector,
        )
        ctx.debate_outcome = outcome
        if xai_collector:
            xai_collector.log_agent_thought(
                "ResponseJudge",
                f"Consensus : {outcome.consensus_action}. Raisonnement : {outcome.final_reasoning}",
            )

        yield StreamStep(
            type="thought",
            content=f"[Swarm] Consensus : {outcome.consensus_action}. Raisonnement : {outcome.final_reasoning}",
        ).model_dump()
        yield StreamStep(type="eval", content=outcome.model_dump()).model_dump()

        action = outcome.consensus_action
        if ctx.iteration >= 10 and action == JudgeAction.REWRITE:
            yield StreamStep(
                type="thought",
                content="[Swarm] Seuil de correction atteint. Livraison de la meilleure réponse actuelle.",
            ).model_dump()
            return RAGState.FINALIZE

        if action == JudgeAction.APPROVE:
            return RAGState.FINALIZE
        elif action == JudgeAction.REWRITE:
            ctx.correction_feedback = f"DÉFAUT DÉTECTÉ: {outcome.final_reasoning}. Corrige en restant fidèle au contexte."
            return RAGState.SYNTHESIZE
        elif action == JudgeAction.RESEARCH_MORE:
            if len(ctx.truth_path) < 200 and not ctx.knowledge_acquired:
                yield StreamStep(
                    type="thought",
                    content="[Judge] Contexte local insuffisant. Bascule vers Librarian pour chercher des infos fraîches...",
                ).model_dump()
                return RAGState.ACQUIRE_KNOWLEDGE
            else:
                return RAGState.RESEARCH
        elif action == JudgeAction.REPLAN:
            return RAGState.PLAN
        else:
            return RAGState.FINALIZE
