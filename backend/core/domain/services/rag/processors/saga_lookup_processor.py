from backend.core.domain.services.rag.processors.base import StateProcessor
from backend.core.domain.entities.ai_schemas import RAGContext, RAGState, StreamStep
from typing import Generator
import logging

logger = logging.getLogger("animetix.rag_workflow")


class SagaLookupProcessor(StateProcessor):
    def __init__(self, saga_agent):
        self.saga_agent = saga_agent

    def process(
        self, ctx: RAGContext, xai_collector=None
    ) -> Generator[dict, None, RAGState]:
        yield StreamStep(
            type="thought", content="[World-Brain] Analyse globale de la saga..."
        ).model_dump()
        logger.info("[World-Brain] Analyse globale de la saga...")

        saga_name = self.saga_agent.lookup_saga(ctx.query)
        if saga_name:
            if xai_collector:
                xai_collector.log_agent_thought(
                    "SagaAgent", f"Saga détectée : {saga_name}"
                )
            ctx.saga_name = saga_name
            logger.info(
                f"[World-Brain] Saga détectée : {saga_name}. Récupération du résumé exécutif..."
            )

            summary = self.saga_agent.get_saga_context(saga_name)
            if summary:
                ctx.truth_path += (
                    f"\n\n### RÉSUMÉ GLOBAL DE LA SAGA ({saga_name}) ###\n{summary}\n"
                )
                logger.info("[World-Brain] Contexte macro-temporel intégré.")
            else:
                logger.info(
                    f"[World-Brain] Aucun résumé trouvé pour la saga {saga_name}."
                )
        else:
            logger.info(
                "[World-Brain] Aucune saga macro-temporelle identifiée pour cette requête."
            )

        if ctx.plan and ctx.plan.requires_graph:
            return RAGState.GRAPH_EXPLORE
        else:
            return RAGState.RESEARCH
