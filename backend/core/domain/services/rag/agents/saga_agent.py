import logging
from typing import Optional
from core.domain.services.llm_service import LLMService
from core.ports.graph_persistence_port import GraphPersistencePort

logger = logging.getLogger("animetix.rag.saga_agent")


class SagaAgent:
    """
    Agent spécialisé dans la récupération du macro-contexte des franchises (Sagas).
    Permet d'obtenir l'Executive Summary global d'une licence.
    """

    def __init__(self, llm_service: LLMService, neo4j_manager: GraphPersistencePort):
        self.llm_service = llm_service
        self.neo4j_manager = neo4j_manager

    def lookup_saga(self, query: str) -> Optional[str]:
        """
        Identifie si la requête porte sur une saga connue.
        Utilise le SLM pour une extraction rapide.
        """
        logger.info(f"🔍 SagaAgent: Looking up saga for query: {query}")
        prompt = f"Extrais UNIQUEMENT le nom de la franchise d'animation mentionnée (ex: 'One Piece', 'Fate') ou réponds 'NONE' : '{query}'"

        try:
            res = self.llm_service.generate(prompt, use_slm=True)
            if not res or "NONE" in res.upper() or len(res) > 30:
                return None

            saga_name = res.strip().strip("'\"")
            logger.info(f"🎯 SagaAgent: Potential saga identified: {saga_name}")
            return saga_name
        except Exception as e:
            logger.error(f"❌ SagaAgent lookup failed: {e}")
            return None

    def get_saga_context(self, saga_name: str) -> Optional[str]:
        """
        Récupère l'executive summary de la saga depuis Neo4j.
        """
        logger.info(f"📚 SagaAgent: Retrieving executive summary for saga: {saga_name}")
        query = "MATCH (s:Saga {name: $name}) RETURN s.executive_summary as summary"

        try:
            results = self.neo4j_manager.execute_query(query, {"name": saga_name})
            if results and results[0].get("summary"):
                logger.info(f"✅ SagaAgent: Summary found for {saga_name}")
                return results[0]["summary"]

            logger.info(f"⚠️ SagaAgent: No summary found for {saga_name}")
            return None
        except Exception as e:
            logger.error(f"❌ SagaAgent context retrieval failed: {e}")
            return None
