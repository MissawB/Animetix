# -*- coding: utf-8 -*-
"""
Hierarchical GraphRAG Service for Animetix.
Uses graph partition detection to summarize global themes and inject them into RAG prompts.
"""

import logging
from typing import List, Dict, Any, Optional
from core.ports.graph_persistence_port import GraphPersistencePort
from core.domain.services.llm_service import LLMService
from pipeline.mlops.graph_community_partitioner import GraphCommunityPartitioner

logger = logging.getLogger("animetix.graphrag")

class HierarchicalGraphRAGService:
    def __init__(self, neo4j_manager: Optional[GraphPersistencePort], llm_service: LLMService):
        self.neo4j_manager = neo4j_manager
        self.llm_service = llm_service
        self.partitioner = GraphCommunityPartitioner(neo4j_manager=neo4j_manager, llm_service=llm_service)
        self._communities_loaded = False

    def ensure_communities_loaded(self):
        """Assure que les communautés thématiques sont chargées et partitionnées."""
        if self._communities_loaded:
            return
        try:
            self.partitioner.run_partitioning()
            self._communities_loaded = True
        except Exception as e:
            logger.error(f"Error initializing partitioner in HierarchicalGraphRAGService: {e}")

    def retrieve_community_contexts(self, query: str, limit: int = 2) -> List[Dict[str, Any]]:
        """
        Recherche les communautés thématiques les plus pertinentes par rapport
        à la requête et renvoie leur résumé macro-conceptuel.
        """
        self.ensure_communities_loaded()
        try:
            matched_communities = self.partitioner.search_communities(query, limit=limit)
            return matched_communities
        except Exception as e:
            logger.error(f"Error retrieving community contexts: {e}")
            return []

    def enrich_prompt_with_graphrag(self, query: str, base_context: str) -> str:
        """
        Enrichit le contexte de base d'une requête RAG avec les concepts globaux
        extraits du graphe de connaissances.
        """
        communities = self.retrieve_community_contexts(query, limit=2)
        if not communities:
            return base_context

        graphrag_context = "\n=== CONTEXTE GLOBAL DU GRAPHE DE CONNAISSANCES (GraphRAG) ===\n"
        for idx, comm in enumerate(communities):
            graphrag_context += f"\n[Communauté Globale #{idx+1} : {comm.get('name')}]\n"
            graphrag_context += f"Résumé thématique : {comm.get('summary')}\n"
            graphrag_context += f"Entités clés : {', '.join(comm.get('entities', []))}\n"

        return base_context + "\n" + graphrag_context
