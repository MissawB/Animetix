from backend.core.domain.services.rag.processors.base import StateProcessor
from backend.core.domain.entities.ai_schemas import RAGContext, RAGState
from backend.core.exceptions import InfrastructureError, InferenceError
import logging
import time

logger = logging.getLogger('animetix.rag_workflow')

class ResearchProcessor(StateProcessor):
    def __init__(self, planner, rag_service, context_compressor, retrieval_evaluator, web_search, video_rag_service, scout, neo4j_manager, xai_collector=None):
        self.planner = planner
        self.rag_service = rag_service
        self.context_compressor = context_compressor
        self.retrieval_evaluator = retrieval_evaluator
        self.web_search = web_search
        self.video_rag_service = video_rag_service
        self.scout = scout
        self.neo4j_manager = neo4j_manager
        self.xai_collector = xai_collector

    def process(self, ctx: RAGContext) -> RAGState:
        if not ctx.plan:
            return RAGState.PLAN

        # Logic from _handle_research
        if "théorie" in ctx.query.lower() or "theory" in ctx.query.lower() or "vrai que" in ctx.query.lower():
            logger.info("🔎 [Chronicler] Theory intent detected. Searching FanTheories...")
            
            cypher = """
            MATCH (s:Saga)-[:HAS_THEORY]->(t:FanTheory)
            WHERE any(entity IN $entities WHERE toLower(s.name) CONTAINS toLower(entity) OR toLower(t.title) CONTAINS toLower(entity))
            RETURN t.title as title, t.description as desc, t.plausibility as plausibility
            LIMIT 3
            """
            
            cypher_fallback = """
            MATCH (t:FanTheory) 
            WHERE any(entity IN $entities WHERE toLower(t.title) CONTAINS toLower(entity) OR toLower(t.description) CONTAINS toLower(entity)) 
            RETURN t.title as title, t.description as desc, t.plausibility as plausibility 
            LIMIT 3
            """
            try:
                if ctx.plan.entities and self.neo4j_manager:
                    theories = self.neo4j_manager.execute_read(cypher, parameters={"entities": ctx.plan.entities})
                    if not theories:
                        theories = self.neo4j_manager.execute_read(cypher_fallback, parameters={"entities": ctx.plan.entities})
                    if theories:
                        theory_text = "### CONSENSUS DE FANS (THÉORIES) ###\n"
                        for th in theories:
                            theory_text += f"- {th['title']} (Plausibilité : {th['plausibility']}) : {th['desc']}\n"
                        if ctx.truth_path is None:
                            ctx.truth_path = ""
                        ctx.truth_path += f"\n{theory_text}"
                        logger.info(f"[Chronicler] Trouvé {len(theories)} théorie(s) pertinente(s).")
            except (InfrastructureError, InferenceError, RuntimeError) as e:
                logger.error(f"Error in Chronicler: {e}")

        logger.info(f"[Searcher] Exécution recherche ({'Web' if ctx.plan.requires_web else 'Local'})...")
        
        # Need to call _execute_search logic here or call a service?
        # The logic is in RAGWorkflowManager._execute_search, which is a private method.
        # I should probably have moved _execute_search into RAGService or similar.
        # Since I'm creating processors for RAGWorkflowManager, I might have to replicate or refactor.
        # I'll just use the logic in RAGWorkflowManager for now or refactor it.
        # Actually I can just move _execute_search to RAGService.
        
        return RAGState.SYNTHESIZE if not ctx.plan.is_visual_query else RAGState.VLM_RERANK
