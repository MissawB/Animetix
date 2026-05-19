import os
import numpy as np
import logging
from typing import List, Dict, Optional
from core.ports.repository_port import RepositoryPort
from .llm_service import LLMService
from .rag.hybrid_index import HybridSearchIndex
from .prompt_manager import PromptManager

logger = logging.getLogger('animetix')

class AdvancedRAGService:
    """
    Service RAG 2.0 combinant recherche hybride, ré-ordonnancement (Reranking)
    et vérification de cohérence (Self-RAG).
    """
    def __init__(self, repository: RepositoryPort, llm_service: LLMService, neo4j_manager=None, reranker=None, prompt_manager: PromptManager = None):
        self.repository = repository
        self.llm_service = llm_service
        self.neo4j_manager = neo4j_manager
        self.reranker = reranker
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
        """Recherche hybride lexicale et sémantique (via chunks contextuels)."""
        idx = self._get_or_create_index(media_type)
        return idx.search(query, limit=limit)

    def rerank_results(self, query: str, candidates: List[Dict]) -> List[Dict]:
        """Ré-ordonne les candidats en utilisant le modèle de cross-encoding et le graphe de connaissances."""
        if not self.reranker or not candidates:
            return candidates
        
        pairs = []
        for c in candidates:
            # Enrichissement via Neo4j si disponible
            graph_info = ""
            if self.neo4j_manager:
                try:
                    connections = self.neo4j_manager.find_logical_connections(c['id'])
                    if connections:
                        graph_info = " | Connexions: " + ", ".join([f"{conn['title']} ({conn['strength']})" for conn in connections])
                except Exception as e:
                    logger.warning(f"Neo4j enrichment failed: {e}")
            
            doc_text = f"Titre: {c.get('title') or c.get('name')} | Description: {c.get('description', '')[:300]}{graph_info}"
            pairs.append([query, doc_text])
            
        try:
            import torch
            with torch.no_grad():
                scores = self.reranker.predict(pairs)
            
            ranked_indices = np.argsort(scores)[::-1]
            return [candidates[i] for i in ranked_indices]
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return candidates

    def generate_advanced_answer(self, query: str, media_type: str) -> str:
        """Processus complet : Search -> Rerank -> Verify -> Generate."""
        candidates = self.hybrid_search(query, media_type, limit=10)
        ranked_candidates = self.rerank_results(query, candidates)
        
        top_results = ranked_candidates[:5]
        context = "\n".join([f"- {r.get('title') or r.get('name')}: {r.get('description', '')[:500]}" for r in top_results])
        
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
        except:
            return True # Par défaut on continue si le juge échoue
