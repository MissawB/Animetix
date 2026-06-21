import logging
from typing import Generator

from core.domain.entities.ai_schemas import RAGContext, RAGState, StreamStep
from core.domain.exceptions import InferenceError, InfrastructureError
from core.domain.services.rag.processors.base import StateProcessor

logger = logging.getLogger("animetix.rag_workflow")


class ResearchProcessor(StateProcessor):
    def __init__(
        self,
        planner,
        rag_service,
        context_compressor,
        retrieval_evaluator,
        web_search,
        scout,
        neo4j_manager,
    ):
        self.planner = planner
        self.rag_service = rag_service
        self.context_compressor = context_compressor
        self.retrieval_evaluator = retrieval_evaluator
        self.web_search = web_search
        self.scout = scout
        self.neo4j_manager = neo4j_manager

    def process(
        self, ctx: RAGContext, xai_collector=None
    ) -> Generator[dict, None, RAGState]:
        if not ctx.plan:
            return RAGState.PLAN

        yield StreamStep(
            type="thought",
            content=f"[Searcher] Exécution recherche ({'Web' if ctx.plan.requires_web else 'Local'})...",
        ).model_dump()

        # Logic from _handle_research
        if (
            "théorie" in ctx.query.lower()
            or "theory" in ctx.query.lower()
            or "vrai que" in ctx.query.lower()
        ):
            yield StreamStep(
                type="thought",
                content="[Chronicler] Vérification des théories de fans dans la base...",
            ).model_dump()
            logger.info(
                "🔎 [Chronicler] Theory intent detected. Searching FanTheories..."
            )

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
                    theories = self.neo4j_manager.execute_read(
                        cypher, parameters={"entities": ctx.plan.entities}
                    )
                    if not theories:
                        theories = self.neo4j_manager.execute_read(
                            cypher_fallback, parameters={"entities": ctx.plan.entities}
                        )
                    if theories:
                        theory_text = "### CONSENSUS DE FANS (THÉORIES) ###\n"
                        for th in theories:
                            theory_text += f"- {th['title']} (Plausibilité : {th['plausibility']}) : {th['desc']}\n"
                        if ctx.truth_path is None:
                            ctx.truth_path = ""
                        ctx.truth_path += f"\n{theory_text}"
                        logger.info(
                            f"[Chronicler] Trouvé {len(theories)} théorie(s) pertinente(s)."
                        )
            except (InfrastructureError, InferenceError, RuntimeError) as e:
                logger.error(f"Error in Chronicler: {e}")

        logger.info(
            f"[Searcher] Exécution recherche ({'Web' if ctx.plan.requires_web else 'Local'})..."
        )

        raw_results = []
        if ctx.plan.requires_web:
            if self.web_search:
                raw_results = self.web_search.search(
                    ctx.plan.optimized_query or ctx.query
                )
            candidates = []
            raw_text_parts = []
            for r in raw_results:
                snippet = r.get("snippet", r.get("content", ""))
                candidates.append(
                    {
                        "title": r.get("title", "Sans titre"),
                        "description": snippet,
                        "image_url": r.get("image_url") or r.get("url"),
                    }
                )
                raw_text_parts.append(f"Title: {r.get('title')}\nSnippet: {snippet}")
            raw_context = "\n\n".join(raw_text_parts)
        else:
            raw_results = self.rag_service.hybrid_search(
                ctx.plan.optimized_query or ctx.query, ctx.media_type
            )
            candidates = raw_results
            raw_text_parts = []
            for r in raw_results:
                desc = r.get("description", "")
                raw_text_parts.append(f"Title: {r.get('title')}\nDescription: {desc}")
            raw_context = "\n\n".join(raw_text_parts)

        ctx.candidates = candidates

        if xai_collector and candidates:
            xai_collector.log_retrieval(candidates)

        distilled = self.scout.find_truth_path(ctx.query, ctx.plan, raw_context)
        if ctx.truth_path:
            ctx.truth_path += f"\n\n### CONTEXTE PRINCIPAL ###\n{distilled}"
        else:
            ctx.truth_path = f"### CONTEXTE PRINCIPAL ###\n{distilled}"

        return (
            RAGState.SYNTHESIZE if not ctx.plan.is_visual_query else RAGState.VLM_RERANK
        )
