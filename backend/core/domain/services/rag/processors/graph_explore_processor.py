from backend.core.domain.services.rag.processors.base import StateProcessor
from backend.core.domain.entities.ai_schemas import RAGContext, RAGState, StreamStep
from typing import Generator
from backend.core.domain.exceptions import InfrastructureError
import logging

logger = logging.getLogger('animetix.rag_workflow')

class GraphExploreProcessor(StateProcessor):
    def __init__(self, community_partitioner, graph_expert, neo4j_manager, xai_collector=None):
        self.community_partitioner = community_partitioner
        self.graph_expert = graph_expert
        self.neo4j_manager = neo4j_manager
        self.xai_collector = xai_collector

    def process(self, ctx: RAGContext) -> Generator[dict, None, RAGState]:
        if not ctx.plan:
            return RAGState.PLAN

        yield StreamStep(type="thought", content="[GraphRAG] Recherche de communautés thématiques transversales...").model_dump()

        logger.info("[GraphRAG] Recherche de communautés thématiques transversales...")
        communities = self.community_partitioner.search_communities(ctx.query)
        if communities:
            comm_ctx = "\n\n### CONTEXTE GRAPHRAG (COMMUNAUTÉS THÉMATIQUES) ###\n"
            for comm in communities:
                comm_ctx += f"- Communauté : {comm['name']}\n  Résumé : {comm['summary']}\n  Entités clés : {', '.join(comm['entities'])}\n"
            if ctx.truth_path is None:
                ctx.truth_path = ""
            ctx.truth_path += comm_ctx
            logger.info(f"[GraphRAG] Intégration de {len(communities)} résumé(s) de communauté(s) macro-conceptuelle(s).")

        if not self.neo4j_manager:
            logger.info("[Graph-Agent] Neo4j non disponible pour l'exploration détaillée. Poursuite avec GraphRAG Communautaire...")
            return RAGState.RESEARCH

        yield StreamStep(type="thought", content="[Graph-Agent] Génération d'une requête Cypher...").model_dump()
        logger.info("[Graph-Agent] Génération d'une requête Cypher...")
        cypher = self.graph_expert.generate_cypher(ctx.query, ctx.plan.reasoning)
        
        if cypher:
            if self.xai_collector:
                self.xai_collector.log_agent_thought("GraphExpert", f"Requête Cypher générée : {cypher}")
            yield StreamStep(type="thought", content=f"[Graph-Agent] Exécution Cypher : {cypher}").model_dump()
            logger.info(f"[Graph-Agent] Exécution Cypher : {cypher}")
            try:
                results = self.neo4j_manager.execute_read(cypher)
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
            logger.info("[Graph-Agent] Impossible de générer une requête Cypher pertinente.")
        
        return RAGState.RESEARCH
