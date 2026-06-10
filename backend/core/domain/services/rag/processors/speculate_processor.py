from backend.core.domain.services.rag.processors.base import StateProcessor
from core.domain.entities.ai_schemas import RAGContext, RAGState
import logging

logger = logging.getLogger('animetix.rag_workflow')

class SpeculateProcessor(StateProcessor):
    def __init__(self, forge, xai_collector=None):
        self.forge = forge
        self.xai_collector = xai_collector

    def process(self, ctx: RAGContext) -> RAGState:
        logger.info("[The Forge] Lancement du moteur de spéculation logique...")
        res = self.forge.generate_hypothesis(ctx.query, ctx.truth_path)
        
        if res and res.hypothesis:
            if self.xai_collector:
                self.xai_collector.log_agent_thought("ForgeAgent", f"Hypothèse générée : {res.hypothesis}")
            logger.info(f"[The Forge] Hypothèse générée : {res.hypothesis}")
            speculation_block = f"\n\n### HYPOTHÈSE LOGIQUE (DÉDUCTION) ###\n"
            speculation_block += f"DÉDUCTION : {res.hypothesis}\n"
            speculation_block += f"RAISONNEMENT : {res.rationale}\n"
            speculation_block += f"NOTE : Cette information est une déduction logique basée sur les données disponibles et peut ne pas être factuelle à 100%.\n"
            ctx.truth_path += speculation_block
        else:
            logger.info("[The Forge] Impossible de forger une hypothèse cohérente.")
            
        return RAGState.SYNTHESIZE
