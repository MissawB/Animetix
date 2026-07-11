import asyncio
import logging

from core.domain.entities.ai_schemas import RAGContext, RAGState, StreamStep
from core.domain.exceptions import InfrastructureError
from core.domain.services.rag.processors.base import StateProcessor

logger = logging.getLogger("animetix.rag_workflow")


class GraphExploreProcessor(StateProcessor):
    def __init__(self, community_partitioner, graph_expert, neo4j_manager):
        self.community_partitioner = community_partitioner
        self.graph_expert = graph_expert
        self.neo4j_manager = neo4j_manager

    async def aprocess(self, ctx: RAGContext, xai_collector=None):
        if not ctx.plan:
            ctx.next_state = RAGState.PLAN
            return

        yield StreamStep(
            type="thought",
            content="[GraphRAG] Recherche de communautés thématiques transversales...",
        ).model_dump()

        logger.info("[GraphRAG] Recherche de communautés thématiques transversales...")
        communities = await asyncio.to_thread(
            self.community_partitioner.search_communities, ctx.query
        )
        if communities:
            comm_ctx = "\n\n### CONTEXTE GRAPHRAG (COMMUNAUTÉS THÉMATIQUES) ###\n"
            for comm in communities:
                comm_ctx += f"- Communauté : {comm['name']}\n  Résumé : {comm['summary']}\n  Entités clés : {', '.join(comm['entities'])}\n"
            if ctx.truth_path is None:
                ctx.truth_path = ""
            ctx.truth_path += comm_ctx
            logger.info(
                f"[GraphRAG] Intégration de {len(communities)} résumé(s) de communauté(s) macro-conceptuelle(s)."
            )

        if not self.neo4j_manager:
            logger.info(
                "[Graph-Agent] Neo4j non disponible pour l'exploration détaillée. Poursuite avec GraphRAG Communautaire..."
            )
            ctx.next_state = RAGState.RESEARCH
            return

        yield StreamStep(
            type="thought", content="[Graph-Agent] Génération d'une requête Cypher..."
        ).model_dump()
        logger.info("[Graph-Agent] Génération d'une requête Cypher...")
        cypher = await asyncio.to_thread(
            self.graph_expert.generate_cypher, ctx.query, ctx.plan.reasoning
        )

        if cypher:
            if xai_collector:
                xai_collector.log_agent_thought(
                    "GraphExpert", f"Requête Cypher générée : {cypher}"
                )
            yield StreamStep(
                type="thought", content=f"[Graph-Agent] Exécution Cypher : {cypher}"
            ).model_dump()
            logger.info(f"[Graph-Agent] Exécution Cypher : {cypher}")
            try:
                results = await asyncio.to_thread(
                    self.neo4j_manager.execute_read, cypher
                )
                if results:
                    res_str = f"\n[Graph-Agent Results]:\n{results}\n"
                    if ctx.truth_path is None:
                        ctx.truth_path = ""
                    ctx.truth_path += res_str
                else:
                    logger.info("[Graph-Agent] Aucun résultat trouvé dans le graphe.")
            except InfrastructureError as e:
                logger.error(f"Graph execution failed: {e}")
            except Exception as e:
                logger.error(f"Unexpected Graph error: {e}")
        else:
            logger.info(
                "[Graph-Agent] Impossible de générer une requête Cypher pertinente."
            )

        ctx.next_state = RAGState.RESEARCH
