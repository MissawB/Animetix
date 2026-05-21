import os
import numpy as np
import logging
from typing import List, Dict, Optional
from core.ports.repository_port import RepositoryPort
from .llm_service import LLMService
from core.utils.lazy_import import lazy_import
from .rag.hybrid_index import HybridSearchIndex
from .prompt_manager import PromptManager

logger = logging.getLogger('animetix')

class AdvancedRAGService:
    """
    Service RAG 2.0 combinant recherche hybride, ré-ordonnancement (Reranking)
    et vérification de cohérence (Self-RAG).
    """
    def __init__(self, repository: RepositoryPort, llm_service: LLMService, neo4j_manager=None, prompt_manager: PromptManager = None):
        self.repository = repository
        self.llm_service = llm_service
        self.neo4j_manager = neo4j_manager
        self.prompt_manager = prompt_manager or getattr(llm_service, 'prompt_manager', None)
        self._indices: Dict[str, HybridSearchIndex] = {}

    def _get_or_create_index(self, media_type: str) -> HybridSearchIndex:
        if media_type not in self._indices:
            idx = HybridSearchIndex()
            catalog = self.repository.load_catalog(media_type)
            if catalog:
                idx.initialize(catalog['db'], media_type)
            self._indices[media_type] = idx
        return self._indices[media_type]

    def hybrid_search(self, query: str, media_type: str, limit: int = 10) -> List[Dict]:
        """Recherche hybride lexicale et sémantique combinée avec Reciprocal Rank Fusion (RRF)."""
        idx = self._get_or_create_index(media_type)
        
        # 1. Recherche lexicale brute (TF-IDF/BM25)
        lexical_results = idx.search(query, limit=limit * 2)
        
        # 2. Recherche sémantique brute (PgVector)
        semantic_results = []
        try:
            semantic_results = self.repository.search_media_items(query, media_type, limit=limit * 2)
        except Exception as e:
            logger.warning(f"Semantic search failed in hybrid search: {e}")
            
        # 3. Fusion des résultats avec RRF
        fused_results = idx.reciprocal_rank_fusion(lexical_results, semantic_results)
        
        return fused_results[:limit]

    def graph_rag_summaries(self, query: str, media_type: str, limit: int = 5) -> str:
        """
        Génère un contexte structuré enrichi par Neo4j (GraphRAG).
        Récupère les entités connectées et synthétise leurs relations.
        """
        if not self.neo4j_manager:
            return ""
            
        try:
            # Recherche d'items proches pour démarrer
            items = self.hybrid_search(query, media_type, limit=3)
            if not items:
                return ""
                
            graph_context = []
            for item in items:
                item_id = item.get('id')
                item_title = item.get('title') or item.get('name')
                
                # Trouver les connexions logiques
                connections = self.neo4j_manager.find_logical_connections(item_id)
                if connections:
                    conn_strs = [f"{c.get('title') or c.get('name')} ({c.get('relationship', 'connexe')})" for c in connections[:limit]]
                    graph_context.append(f"Relations pour '{item_title}': {', '.join(conn_strs)}")
            
            if graph_context:
                return "\n[GraphRAG Context]\n" + "\n".join(graph_context) + "\n"
        except Exception as e:
            logger.warning(f"GraphRAG extraction failed: {e}")
            
        return ""

    def rerank_results(self, query: str, candidates: List[Dict]) -> List[Dict]:
        """Ré-ordonne les candidats en utilisant le modèle de cross-encoding de l'InferencePort."""
        if not candidates:
            return candidates
        
        texts_to_score = []
        for c in candidates:
            graph_info = ""
            if self.neo4j_manager:
                try:
                    connections = self.neo4j_manager.find_logical_connections(c['id'])
                    if connections:
                        graph_info = " | Connexions: " + ", ".join([f"{conn['title']} ({conn['strength']})" for conn in connections])
                except Exception as e:
                    logger.warning(f"Neo4j enrichment failed: {e}")
            
            doc_text = f"Titre: {c.get('title') or c.get('name')} | Description: {c.get('description', '')[:300]}{graph_info}"
            texts_to_score.append(doc_text)
            
        try:
            scores = self.llm_service.inference_engine.rerank_documents(query, texts_to_score)
            ranked_indices = np.argsort(scores)[::-1]
            return [candidates[i] for i in ranked_indices]
        except Exception as e:
            logger.error(f"Reranking via InferencePort failed: {e}")
            return candidates

    def generate_advanced_answer(self, query: str, media_type: str) -> str:
        """Processus complet : Search -> Rerank (RRF) -> GraphRAG -> Verify -> Generate."""
        candidates = self.hybrid_search(query, media_type, limit=10)
        ranked_candidates = self.rerank_results(query, candidates)
        
        top_results = ranked_candidates[:5]
        context = "\n".join([f"- {r.get('title') or r.get('name')}: {r.get('description', '')[:500]}" for r in top_results])
        
        # Enchevêtrement du contexte GraphRAG
        graph_ctx = self.graph_rag_summaries(query, media_type)
        if graph_ctx:
            context += graph_ctx
            
        # Validation Self-RAG
        if not self.self_rag_verify(query, context):
            logger.info(f"Self-RAG: Context insufficient for query '{query}'")
            # Ici on pourrait ajouter une logique de recherche web fallback
            
        prompt, system_prompt = self.prompt_manager.get_prompt("advanced_rag_generate", context=context, query=query)
        return self.llm_service.inference_engine.generate(prompt, system_prompt=system_prompt)

    def self_rag_verify(self, query: str, context: str) -> bool:
        """Vérifie si le contexte fourni permet de répondre à la question (évite les hallucinations)."""
        prompt, _ = self.prompt_manager.get_prompt("self_rag_verify", context=context, query=query)
        try:
            res = self.llm_service.inference_engine.generate(prompt)
            return "OUI" in res.upper()
        except Exception as e:
            logger.warning(f"Self-RAG verification failed: {e}")
            return True # Par défaut on continue si le juge échoue
