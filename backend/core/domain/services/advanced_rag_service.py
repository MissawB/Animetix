import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from core.ports.generic_cache_port import CachePort, InMemoryCache
from core.ports.graph_persistence_port import GraphPersistencePort
from core.ports.repository_port import RepositoryPort

from .llm_service import LLMService
from .prompt_manager import PromptManager
from .rag.hybrid_index import HybridSearchIndex
from .rag.rerank_cache import RerankingCache

logger = logging.getLogger("animetix")


class AdvancedRAGService:
    """
    Service RAG 2.0 combinant recherche hybride, ré-ordonnancement (Reranking)
    et vérification de cohérence (Self-RAG).
    Maintenant boosté par des modèles cognitifs (Quantique + Neuromorphique).
    """

    GENRE_TO_CONCEPT = {
        "action": 0,
        "romance": 1,
        "sci-fi": 2,
        "science-fiction": 2,
        "comedy": 3,
        "comedie": 3,
        "drama": 4,
        "drame": 4,
        "fantasy": 5,
        "fantastique": 5,
        "slice of life": 6,
        "tranche de vie": 6,
        "horror": 7,
        "horreur": 7,
        "mystery": 8,
        "mystere": 8,
        "adventure": 9,
        "aventure": 9,
    }

    def __init__(
        self,
        repository: RepositoryPort,
        llm_service: LLMService,
        neo4j_manager: Optional[GraphPersistencePort] = None,
        prompt_manager: Optional[PromptManager] = None,
        colbert_adapter=None,
        quantum_model: Any = "default",
        plasticity_simulator: Any = "default",
        lnn_service: Any = "default",
        cache_port: Optional[CachePort] = None,
        cognitive_boosters_enabled: bool = True,
    ):
        self.repository = repository
        self.llm_service = llm_service
        self.neo4j_manager = neo4j_manager
        self.prompt_manager = prompt_manager or getattr(
            llm_service, "prompt_manager", None
        )
        self.colbert_adapter = colbert_adapter

        # On utilise "default" comme sentinelle pour différencier None (désactivé) de non-fourni
        self._injected_quantum = quantum_model
        self._injected_plasticity = plasticity_simulator
        self._injected_lnn = lnn_service

        self.cache = cache_port or InMemoryCache()
        self.cognitive_boosters_enabled = cognitive_boosters_enabled

        self._indices: Dict[str, HybridSearchIndex] = {}
        self.rerank_cache = RerankingCache(cache_port=self.cache)

    def _get_cognitive_models(
        self, user_id: Optional[str] = None
    ) -> Tuple[Any, Any, Any]:
        """Charge ou initialise les modèles cognitifs spécifiques à l'utilisateur."""
        if not self.cognitive_boosters_enabled:
            return None, None, None
        # 1. Gestion des modèles injectés (ou désactivés via None)
        q = self._injected_quantum
        p = self._injected_plasticity
        lnn_layer = self._injected_lnn

        # Si explicitement None, on désactive
        if q is None and p is None:
            return None, None, None

        # Si injectés (et non "default"), on les utilise
        if q != "default" and p != "default":
            from core.domain.services.neuromorphic_lnn_service import (  # noqa: E402
                LiquidNeuralNetworkService,
            )

            lnn = (
                lnn_layer
                if lnn_layer != "default"
                else LiquidNeuralNetworkService(4, 2)
            )
            return q, p, lnn

        # 2. Sinon, on va chercher dans le cache ou on crée par défaut
        from core.domain.services.neuromorphic_lnn_service import (  # noqa: E402
            LiquidNeuralNetworkService,
        )
        from core.domain.services.neuromorphic_plasticity_service import (  # noqa: E402
            SynapticPlasticityService,
        )
        from core.domain.services.quantum_cognitive_service import (  # noqa: E402
            QuantumCognitiveService,
        )

        if not user_id:
            return (
                QuantumCognitiveService(dimension=4),
                SynapticPlasticityService(num_concepts=10),
                LiquidNeuralNetworkService(state_dimension=4, input_dimension=2),
            )

        state_data = self.cache.get(f"cognitive_state_{user_id}")

        if state_data:
            try:
                quantum = QuantumCognitiveService.from_dict(state_data["quantum"])
                plasticity = SynapticPlasticityService.from_dict(
                    state_data["plasticity"]
                )
                lnn = LiquidNeuralNetworkService.from_dict(state_data["lnn"])
                return quantum, plasticity, lnn
            except Exception as e:
                logger.warning(
                    f"⚠️ Failed to restore cognitive state for {user_id}: {e}"
                )

        return (
            QuantumCognitiveService(dimension=4),
            SynapticPlasticityService(num_concepts=10),
            LiquidNeuralNetworkService(state_dimension=4, input_dimension=2),
        )

    def set_cognitive_boosters(self, enabled: bool) -> None:
        """Active/désactive les boosters cognitifs à chaud (utilisé par l'ablation)."""
        self.cognitive_boosters_enabled = enabled

    def _save_cognitive_models(
        self, user_id: str, quantum_model, plasticity_service, lnn_service
    ):
        if (
            not user_id
            or not quantum_model
            or not plasticity_service
            or not lnn_service
        ):
            return
        state_data = {
            "quantum": quantum_model.to_dict(),
            "plasticity": plasticity_service.to_dict(),
            "lnn": lnn_service.to_dict(),
            "last_updated": time.time(),
        }
        self.cache.set(f"cognitive_state_{user_id}", state_data, timeout=86400 * 30)

    def update_cognitive_state(
        self, user_id: Optional[str], query: str, clicked_item_metadata: Dict[str, Any]
    ):
        """Boucle de feedback réelle."""
        quantum_model, plasticity_service, lnn_service = self._get_cognitive_models(
            user_id
        )
        if not quantum_model or not plasticity_service or not lnn_service:
            return

        q_lower = query.lower()
        query_concepts = [
            self.GENRE_TO_CONCEPT[g] for g in self.GENRE_TO_CONCEPT if g in q_lower
        ]

        item_genres = [g.lower() for g in clicked_item_metadata.get("genres", [])]
        item_concepts = [
            self.GENRE_TO_CONCEPT[g] for g in item_genres if g in self.GENRE_TO_CONCEPT
        ]

        # Hebbian
        activations = [0.0] * plasticity_service.num_concepts
        for cid in list(set(query_concepts + item_concepts)):
            if 0 <= cid < len(activations):
                activations[cid] = 1.0
        plasticity_service.update_hebbian(activations, learning_rate=0.05)

        # STDP
        if query_concepts and item_concepts:
            now = time.time()
            plasticity_service.trigger_spikes(query_concepts, now - 0.05)
            plasticity_service.trigger_spikes(item_concepts, now)
            for pre in query_concepts:
                for post in item_concepts:
                    if pre != post:
                        plasticity_service.update_stdp(pre, post, learning_rate=0.1)

        # Quantum Born Measure
        mapping = {
            "shonen": "shonen",
            "seinen": "seinen",
            "ghibli": "ghibli",
            "comedy": "comedy",
        }
        quantum_theme = next((mapping[k] for k in mapping if k in item_genres), None)
        if quantum_theme:
            quantum_model.measure_preference(quantum_theme)

        # LNN Vibe
        shonen_vibe = 1.0 if "shonen" in q_lower else 0.0
        seinen_vibe = 1.0 if "seinen" in q_lower else 0.0
        lnn_service.process_continuous_signal([[shonen_vibe, seinen_vibe]], dt=0.1)

        if user_id:
            self._save_cognitive_models(
                user_id, quantum_model, plasticity_service, lnn_service
            )
        logger.info(f"🔄 Cognitive state updated for user {user_id or 'anonymous'}")

    def hybrid_search(
        self,
        query: str,
        media_type: str,
        limit: int = 10,
        user_id: Optional[str] = None,
    ) -> List[Dict]:
        idx = self._get_or_create_index(media_type)
        lexical_results = idx.search(query, limit=limit * 2)
        semantic_results = []
        try:
            semantic_results = self.repository.search_media_items(
                query, media_type, limit=limit * 2
            )
        except Exception as e:
            logger.warning(f"Semantic search failed: {e}")

        fused_results = idx.reciprocal_rank_fusion(lexical_results, semantic_results)
        fused_results = self._adjust_scores_cognitively(
            fused_results, query, user_id=user_id
        )
        return fused_results[:limit]

    def _get_or_create_index(self, media_type: str) -> HybridSearchIndex:
        if media_type not in self._indices:
            idx = HybridSearchIndex()
            catalog = self.repository.load_catalog(media_type)
            if catalog:
                idx.initialize(catalog["db"], media_type)
            self._indices[media_type] = idx
        return self._indices[media_type]

    def rerank_results(
        self, query: str, candidates: List[Dict], user_id: Optional[str] = None
    ) -> List[Dict]:
        if not candidates:
            return candidates
        doc_ids = [str(c["id"]) for c in candidates]
        cached_scores = self.rerank_cache.get_scores(query, doc_ids)
        to_compute = []
        final_scores = {}
        for c in candidates:
            cid = str(c["id"])
            if cid in cached_scores:
                final_scores[cid] = cached_scores[cid]
            else:
                to_compute.append(c)

        if not to_compute:
            return sorted(
                candidates,
                key=lambda x: final_scores.get(str(x["id"]), 0.0),
                reverse=True,
            )

        texts_to_score = [
            f"Titre: {c.get('title')} | {c.get('description', '')[:300]}"
            for c in to_compute
        ]
        try:
            new_scores = self.llm_service.inference_engine.rerank_documents(
                query, texts_to_score
            )
            for i, c in enumerate(to_compute):
                final_scores[str(c["id"])] = new_scores[i]
            sorted_candidates = sorted(
                candidates,
                key=lambda x: final_scores.get(str(x["id"]), 0.0),
                reverse=True,
            )
            return self._adjust_scores_cognitively(
                sorted_candidates, query, user_id=user_id
            )
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return self._adjust_scores_cognitively(candidates, query, user_id=user_id)

    def generate_advanced_answer(
        self, query: str, media_type: str, user_id: Optional[str] = None
    ) -> str:
        answer, _ = self.generate_advanced_answer_with_context(
            query, media_type, user_id=user_id
        )
        return answer

    def generate_advanced_answer_with_context(
        self, query: str, media_type: str, user_id: Optional[str] = None
    ) -> Tuple[str, str]:
        candidates = self.hybrid_search(query, media_type, limit=20, user_id=user_id)
        if self.colbert_adapter:
            candidates = self.colbert_adapter.rank_documents(query, candidates)
        ranked_candidates = self.rerank_results(query, candidates, user_id=user_id)
        top_results = ranked_candidates[:5]
        context = "\n".join(
            [
                f"- {r.get('title')}: {r.get('description', '')[:500]}"
                for r in top_results
            ]
        )
        if self.prompt_manager is None:
            logger.error("No prompt_manager configured; cannot generate answer.")
            return "", context
        prompt, system_prompt = self.prompt_manager.get_prompt(
            "advanced_rag_generate", context=context, query=query
        )
        inference_res = self.llm_service.inference_engine.generate(
            prompt, system_prompt=system_prompt
        )
        return inference_res.text, context

    def generate_holistic_answer(
        self, query: str, media_type: str, category_name: str
    ) -> str:
        """Génère une réponse globale en utilisant un résumé de communauté Neo4j comme contexte."""
        if not self.neo4j_manager:
            return ""
        context = self.neo4j_manager.get_community_summary(media_type, category_name)
        if self.prompt_manager is None:
            logger.error("No prompt_manager configured; cannot generate answer.")
            return ""
        prompt, system_prompt = self.prompt_manager.get_prompt(
            "advanced_rag_generate", context=context, query=query
        )
        inference_res = self.llm_service.inference_engine.generate(
            prompt, system_prompt=system_prompt
        )
        return inference_res.text

    def _adjust_scores_cognitively(
        self, candidates: List[Dict], query: str, user_id: Optional[str] = None
    ) -> List[Dict]:
        if not candidates:
            return candidates

        quantum_model, plasticity_service, lnn_service = self._get_cognitive_models(
            user_id
        )
        if not quantum_model or not plasticity_service or not lnn_service:
            return candidates

        query_concepts = [
            self.GENRE_TO_CONCEPT[g]
            for g in self.GENRE_TO_CONCEPT
            if g in query.lower()
        ]
        lnn_variance = np.var(lnn_service.state)
        attention_modulation = 1.0 / (1.0 + lnn_variance)

        adjusted_candidates = []
        alpha = 0.3 * attention_modulation
        beta = 0.5

        for candidate in candidates:
            genres = [g.lower() for g in candidate.get("genres", [])]

            # Plasticité
            candidate_concepts = [
                self.GENRE_TO_CONCEPT[g] for g in genres if g in self.GENRE_TO_CONCEPT
            ]
            plastic_score = 0.0
            if candidate_concepts:
                weights = []
                for c_d in candidate_concepts:
                    if query_concepts:
                        for c_q in query_concepts:
                            weights.append(plasticity_service.W[c_q, c_d])
                    else:
                        weights.append(np.mean(plasticity_service.W[:, c_d]))
                plastic_score = np.mean(weights) if weights else 0.0

            # Quantique
            mapping = {
                "shonen": "shonen",
                "seinen": "seinen",
                "ghibli": "ghibli",
                "comedy": "comedy",
            }
            quantum_theme = next((mapping[k] for k in mapping if k in genres), None)
            quantum_score = 0.5
            if quantum_theme:
                P = quantum_model.projectors.get(quantum_theme)
                if P is not None:
                    quantum_model.state /= np.linalg.norm(quantum_model.state) or 1.0
                    quantum_score = float(
                        np.real(
                            np.dot(
                                np.conj(quantum_model.state),
                                np.dot(P, quantum_model.state),
                            )
                        )
                    )

            cog_multiplier = beta * plastic_score + (1.0 - beta) * quantum_score
            base_score = candidate.get("score") or 0.5
            final_score = base_score * (1.0 + alpha * cog_multiplier)

            adjusted_cand = dict(candidate)
            adjusted_cand["score"] = round(final_score, 4)
            adjusted_cand["cognitive_boost"] = round(cog_multiplier, 4)
            adjusted_candidates.append(adjusted_cand)

        return sorted(
            adjusted_candidates, key=lambda x: x.get("score", 0.0), reverse=True
        )
