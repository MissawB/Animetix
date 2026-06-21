import logging
from typing import Generator

from core.domain.entities.ai_schemas import RAGContext, RAGState, StreamStep
from core.domain.services.rag.processors.base import StateProcessor

logger = logging.getLogger("animetix.rag_workflow")


class SpeculateProcessor(StateProcessor):
    def __init__(self, forge):
        self.forge = forge

    def process(
        self, ctx: RAGContext, xai_collector=None
    ) -> Generator[dict, None, RAGState]:
        yield StreamStep(
            type="thought",
            content="[The Forge] Lancement du moteur de spéculation logique...",
        ).model_dump()
        logger.info("[The Forge] Lancement du moteur de spéculation logique...")
        res = self.forge.generate_hypothesis(ctx.query, ctx.truth_path)

        if res and res.hypothesis:
            if xai_collector:
                xai_collector.log_agent_thought(
                    "ForgeAgent", f"Hypothèse générée : {res.hypothesis}"
                )
            logger.info(f"[The Forge] Hypothèse générée : {res.hypothesis}")
            yield StreamStep(
                type="thought",
                content=f"[The Forge] Hypothèse générée : {res.hypothesis}",
            ).model_dump()
            speculation_block = "\n\n### HYPOTHÈSE LOGIQUE (DÉDUCTION) ###\n"
            speculation_block += f"DÉDUCTION : {res.hypothesis}\n"
            speculation_block += f"RAISONNEMENT : {res.rationale}\n"
            speculation_block += "NOTE : Cette information est une déduction logique basée sur les données disponibles et peut ne pas être factuelle à 100%.\n"
            ctx.truth_path += speculation_block
        else:
            logger.info("[The Forge] Impossible de forger une hypothèse cohérente.")

        return RAGState.SYNTHESIZE
