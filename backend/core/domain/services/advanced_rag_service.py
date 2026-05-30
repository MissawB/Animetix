import os
import numpy as np
import logging
from typing import List, Dict, Optional, Any
from core.ports.repository_port import RepositoryPort
from core.ports.graph_persistence_port import GraphPersistencePort
from ..exceptions import InfrastructureError, ParsingError, InferenceError
from .llm_service import LLMService
from .rag.hybrid_index import HybridSearchIndex
from .rag.rerank_cache import RerankingCache
from .prompt_manager import PromptManager

logger = logging.getLogger('animetix')

class AdvancedRAGService:
    """
    Service RAG 2.0 combinant recherche hybride, ré-ordonnancement (Reranking)
    et vérification de cohérence (Self-RAG).
    """
    GENRE_TO_CONCEPT = {
        "action": 0, "romance": 1, "sci-fi": 2, "science-fiction": 2,
        "comedy": 3, "comedie": 3, "drama": 4, "drame": 4,
        "fantasy": 5, "fantastique": 5, "slice of life": 6, "tranche de vie": 6,
        "horror": 7, "horreur": 7, "mystery": 8, "mystere": 8,
        "adventure": 9, "aventure": 9
    }

    def __init__(
        self,
        repository: RepositoryPort,
        llm_service: LLMService,
        neo4j_manager: Optional[GraphPersistencePort] = None,
        prompt_manager: PromptManager = None,
        colbert_adapter=None,
        quantum_model: Optional[Any] = None,
        plasticity_simulator: Optional[Any] = None
    ):
        self.repository = repository
        self.llm_service = llm_service
        self.neo4j_manager = neo4j_manager
        self.prompt_manager = prompt_manager or getattr(llm_service, 'prompt_manager', None)
        self.colbert_adapter = colbert_adapter
        self.quantum_model = quantum_model
        self.plasticity_simulator = plasticity_simulator
        self._indices: Dict[str, HybridSearchIndex] = {}
        self.rerank_cache = RerankingCache()

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
        
        # 2. Recherche sémantique brute (ChromaDB)
        semantic_results = []
        try:
            semantic_results = self.repository.search_media_items(query, media_type, limit=limit * 2)
        except InfrastructureError as e:
            logger.warning(f"Semantic search failed in hybrid search: {e}", extra={'context': {'query': query, 'media_type': media_type}})
        except Exception as e:
            logger.error(
                f"Unexpected error in semantic search: {e}", 
                extra={'context': {'query': query, 'media_type': media_type, 'error': str(e)}}
            )
            
        # 3. Fusion des résultats avec RRF
        fused_results = idx.reciprocal_rank_fusion(lexical_results, semantic_results)
        
        # 4. Ajustement cognitif dynamique
        fused_results = self._adjust_scores_cognitively(fused_results, query)
        
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
        except InfrastructureError as e:
            logger.warning(f"GraphRAG extraction failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in GraphRAG summaries: {e}")
            
        return ""


    def rerank_results(self, query: str, candidates: List[Dict]) -> List[Dict]:
        """
        Ré-ordonne les candidats de manière optimisée (Cache + Batching).
        """
        if not candidates:
            return candidates
        
        # 1. Vérification du Cache
        doc_ids = [str(c['id']) for c in candidates]
        cached_scores = self.rerank_cache.get_scores(query, doc_ids)
        
        to_compute = []
        final_scores = {}
        
        for c in candidates:
            cid = str(c['id'])
            if cid in cached_scores:
                final_scores[cid] = cached_scores[cid]
            else:
                to_compute.append(c)
        
        if not to_compute:
            # Tout est en cache, on trie et on sort
            return sorted(candidates, key=lambda x: final_scores.get(str(x['id']), 0.0), reverse=True)

        # 2. Préparation des textes pour le calcul restant
        texts_to_score = []
        for c in to_compute:
            graph_info = ""
            if self.neo4j_manager:
                try:
                    connections = self.neo4j_manager.find_logical_connections(c['id'])
                    if connections:
                        graph_info = " | Connexions: " + ", ".join([f"{conn['title']} ({conn['strength']})" for conn in connections])
                except Exception as e:
                    logger.error("Error fetching logical connections for candidate %s: %s", c.get('id'), e, exc_info=True)
            
            doc_text = f"Titre: {c.get('title') or c.get('name')} | Description: {c.get('description', '')[:300]}{graph_info}"
            texts_to_score.append(doc_text)
            
        try:
            # 3. Calcul par lot via InferencePort
            new_scores = self.llm_service.inference_engine.rerank_documents(query, texts_to_score)
            
            # Mise à jour des scores et du cache
            scores_to_cache = {}
            for i, c in enumerate(to_compute):
                cid = str(c['id'])
                score = new_scores[i]
                final_scores[cid] = score
                scores_to_cache[cid] = score
                
            self.rerank_cache.set_scores(query, scores_to_cache)
            
            # 4. Tri final
            sorted_candidates = sorted(candidates, key=lambda x: final_scores.get(str(x['id']), 0.0), reverse=True)
            return self._adjust_scores_cognitively(sorted_candidates, query)
            
        except Exception as e:
            logger.error(f"Reranking optimization failed: {e}")
            return self._adjust_scores_cognitively(candidates, query)

    def generate_advanced_answer(self, query: str, media_type: str) -> str:
        # 1. Fetch wide candidate pool
        candidates = self.hybrid_search(query, media_type, limit=20)
        
        # 2. Optional: ColBERT Late-Interaction filtering
        if self.colbert_adapter and len(candidates) > 10:
            candidates = self.colbert_adapter.rank_documents(query, candidates)[:10]
            
        # 3. Heavy Cross-Encoder Reranking
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

    def generate_holistic_answer(self, query: str, media_type: str, category_name: str) -> str:
        """
        Exploite les communautés de graphe (Hierarchical GraphRAG) pour répondre
        à des questions macroscopiques ou holistiques.
        """
        if not self.neo4j_manager:
            return "Hierarchical GraphRAG requires Neo4j connection."
            
        community_summary = self.neo4j_manager.get_community_summary(media_type, category_name)
        
        if not community_summary:
            return "No community summary found for this category."
            
        context = f"[Community Summary: {category_name}]\n{community_summary}\n"
        
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

    def _adjust_scores_cognitively(self, candidates: List[Dict], query: str) -> List[Dict]:
        if not candidates:
            return candidates
        if not self.quantum_model and not self.plasticity_simulator:
            return candidates

        # 1. Identifier les concepts stimulés par la requête
        query_concepts = []
        q_lower = query.lower()
        for genre, cid in self.GENRE_TO_CONCEPT.items():
            if genre in q_lower:
                query_concepts.append(cid)

        adjusted_candidates = []
        alpha = 0.3 # Force du biais cognitif
        beta = 0.5  # Équilibre entre plasticité (0.5) et quantique (0.5)

        for candidate in candidates:
            # Récupérer les thèmes et genres du candidat
            genres = [g.lower() for g in candidate.get("genres", [])]
            # Si "genres" n'est pas fourni, on tente de les extraire de la description ou du titre
            desc_lower = candidate.get("description", "").lower()
            title_lower = (candidate.get("title") or candidate.get("name") or "").lower()
            for genre in self.GENRE_TO_CONCEPT:
                if genre not in genres and (genre in desc_lower or genre in title_lower):
                    genres.append(genre)

            # --- A. Partie Plastique (Simulator) ---
            plastic_score = 0.0
            if self.plasticity_simulator:
                candidate_concepts = [self.GENRE_TO_CONCEPT[g] for g in genres if g in self.GENRE_TO_CONCEPT]
                if candidate_concepts:
                    weights = []
                    for c_d in candidate_concepts:
                        if query_concepts:
                            # Moyenne des poids synaptiques pré-synaptiques (query) vers post-synaptiques (document)
                            for c_q in query_concepts:
                                weights.append(self.plasticity_simulator.W[c_q, c_d])
                        else:
                            # Si pas de concept dans la requête, utiliser la moyenne d'attention globale
                            weights.append(np.mean(self.plasticity_simulator.W[:, c_d]))
                    plastic_score = np.mean(weights) if weights else 0.0

            # --- B. Partie Quantique (Preference Model) ---
            quantum_score = 0.0
            if self.quantum_model:
                # Mappage des genres aux 4 thèmes quantiques supportés
                quantum_theme = None
                if "shonen" in genres or "shounen" in genres:
                    quantum_theme = "shonen"
                elif "seinen" in genres:
                    quantum_theme = "seinen"
                elif "ghibli" in genres or "fantasy" in genres:
                    quantum_theme = "ghibli"
                elif "comedy" in genres or "comédie" in genres:
                    quantum_theme = "comedy"

                if quantum_theme:
                    # Règle de Born : calcul de la probabilité sans effondrer l'état
                    P = self.quantum_model.projectors.get(quantum_theme)
                    if P is not None:
                        # p = <psi| P |psi>
                        self.quantum_model.state /= np.linalg.norm(self.quantum_model.state)
                        quantum_score = float(np.real(np.dot(np.conj(self.quantum_model.state), np.dot(P, self.quantum_model.state))))
                else:
                    quantum_score = 0.5 # Neutre

            # --- C. Combinaison Cognitive ---
            cog_multiplier = beta * plastic_score + (1.0 - beta) * quantum_score
            
            # Ajustement du score du candidat (nous créons ou ajustons la clé 'score')
            base_score = candidate.get("score")
            # Si le score de base est nul ou absent (ex: PgVector renvoie des distances), on utilise un score neutre de 0.5
            if base_score is None:
                base_score = 0.5
            
            # Application de la formule : score_final = score_base * (1.0 + alpha * cog_multiplier)
            final_score = base_score * (1.0 + alpha * cog_multiplier)
            
            # Copie profonde légère pour éviter de modifier le candidat original par effet de bord
            adjusted_cand = dict(candidate)
            adjusted_cand["score"] = round(final_score, 4)
            adjusted_cand["cognitive_boost"] = round(cog_multiplier, 4)
            adjusted_candidates.append(adjusted_cand)

        # Trier à nouveau les candidats selon le nouveau score cognitif ajusté
        return sorted(adjusted_candidates, key=lambda x: x.get("score", 0.0), reverse=True)
