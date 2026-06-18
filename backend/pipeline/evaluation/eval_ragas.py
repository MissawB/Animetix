import asyncio
import logging
import os

# --- DJANGO SETUP FOR MLOPS CONTAINERS ---
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pipeline.chroma_client import chroma_manager
from pipeline.neo4j_client import neo4j_manager

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import django  # noqa: E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "animetix_project.settings")
django.setup()

from animetix.containers import get_container  # noqa: E402
from core.domain.services.ragas_eval_service import (  # noqa: E402
    EvaluationResult,
    RagasEvalService,
)
from core.utils.security import safe_http_request  # noqa: E402
from sentence_transformers import SentenceTransformer  # noqa: E402

logger = logging.getLogger("animetix." + __name__)


class RAGEvaluator:
    def __init__(self, brain_url: Optional[str] = None):
        self.brain_url = brain_url or os.getenv(
            "BRAIN_API_URL", "http://127.0.0.1:7861"
        )
        # Assurez-vous que l'URL se termine par /generate
        if not self.brain_url.endswith("/generate"):
            self.brain_url = f"{self.brain_url}/generate"

        self.brain_api_key = os.getenv("BRAIN_API_KEY", "dev-secret-key")
        self.embed_model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")

    def get_contexts(self, query: str, mode: str = "vector") -> List[str]:
        """Récupère le contexte. Mode: 'vector' ou 'hybrid'."""
        contexts, _ = self.get_contexts_with_ids(query, mode=mode)
        return contexts

    def get_contexts_with_ids(
        self, query: str, mode: str = "vector"
    ) -> Tuple[List[str], List[str]]:
        """Récupère le contexte et les IDs de chunks/médias associés."""
        query_embedding = self.embed_model.encode([query]).tolist()
        try:
            results = chroma_manager.query_collection(
                "anime_thematic", query_embedding, n_results=3
            )
            vector_contexts = [
                doc for doc in results["documents"][0] if doc is not None
            ]
            media_ids = [str(res) for res in results["ids"][0] if res is not None]
        except Exception as e:
            logger.error(f"Failed to query contexts for '{query}': {e}")
            vector_contexts = ["Pas de contexte trouvé."]
            media_ids = []

        if mode == "vector":
            return vector_contexts, media_ids

        # 2. Retrieval Graph (Neo4j) - Enrichissement
        try:
            graph_context = neo4j_manager.get_enriched_context(media_ids)
            if graph_context:
                return (
                    vector_contexts
                    + [f"Informations Graph complémentaires:\n{graph_context}"],
                    media_ids,
                )
        except Exception as e:
            logger.warning(f"Neo4j graph enrichment failed: {e}")

        return vector_contexts, media_ids

    def calculate_deterministic_metrics(
        self,
        retrieved_contexts: List[str],
        retrieved_ids: List[str],
        expected_contexts: List[str],
        expected_chunks: List[str],
    ) -> Dict[str, float]:
        """Calcule de manière déterministe les métriques de Context Recall et Context Precision."""
        # --- Context Recall ---
        recall = 1.0
        if expected_contexts:
            hits = 0
            for expected in expected_contexts:
                if any(
                    expected.lower().strip() in retrieved.lower()
                    for retrieved in retrieved_contexts
                ):
                    hits += 1
            recall = hits / len(expected_contexts)
        elif expected_chunks:
            hits = len(set(retrieved_ids) & set(expected_chunks))
            recall = hits / len(expected_chunks) if expected_chunks else 0.0

        # --- Context Precision ---
        precision = 1.0
        if expected_contexts:
            ap_sum = 0.0
            matched_ranks = 0
            for k, retrieved in enumerate(retrieved_contexts):
                is_relevant = any(
                    expected.lower().strip() in retrieved.lower()
                    for expected in expected_contexts
                )
                if is_relevant:
                    matched_ranks += 1
                    precision_at_k = matched_ranks / (k + 1)
                    ap_sum += precision_at_k
            precision = ap_sum / len(expected_contexts) if expected_contexts else 0.0
        elif expected_chunks:
            ap_sum = 0.0
            matched_ranks = 0
            for k, rid in enumerate(retrieved_ids):
                if rid in expected_chunks:
                    matched_ranks += 1
                    precision_at_k = matched_ranks / (k + 1)
                    ap_sum += precision_at_k
            precision = ap_sum / len(expected_chunks) if expected_chunks else 0.0

        return {
            "deterministic_context_recall": recall,
            "deterministic_context_precision": precision,
        }

    def generate_answer(
        self, query: str, contexts: List[str], history: List[Dict[str, str]] = None
    ) -> str:
        """Appelle l'API brain pour générer une réponse avec le contexte et l'historique de dialogue."""
        context_str = "\n".join(contexts)

        # Support multi-turn history
        history_str = ""
        if history:
            for turn in history:
                role = "User" if turn["role"] == "user" else "Assistant"
                history_str += f"{role}: {turn['content']}\n"

        prompt = f"Contexte:\n{context_str}\n\n"
        if history_str:
            prompt += f"Historique de la conversation:\n{history_str}\n"
        prompt += f"Question: {query}"

        try:
            response = safe_http_request(
                "POST",
                self.brain_url,
                json={
                    "prompt": prompt,
                    "system_prompt": "Tu es un expert en Anime/Manga. Utilise le contexte fourni pour répondre de manière précise.",
                },
                headers={"X-API-Key": self.brain_api_key},
                timeout=60,
                allow_internal=True,
            )
            if response.status_code == 200:
                return response.json().get("text", "")
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
        return "Erreur de génération."

    async def run_evaluation(
        self, test_questions: List[Dict[str, str]], mode: str = "vector"
    ):
        """Lance l'évaluation RAGAS sur un set de questions."""
        logger.info(f"🚀 Starting evaluation in mode: {mode.upper()}")
        data = {
            "question": [],
            "answer": [],
            "contexts": [],
            "retrieved_ids": [],
            "ground_truth": [],
            "expected_contexts": [],
            "expected_chunks": [],
        }

        for item in test_questions:
            # support either question/query and ground_truth keys
            q = item.get("question", item.get("query", ""))
            gt = item.get("ground_truth", item.get("expected_title", ""))
            history = item.get("multi_turn_history", [])

            logger.info(f"🧐 Evaluating: {q}")
            contexts, retrieved_ids = self.get_contexts_with_ids(q, mode=mode)
            answer = self.generate_answer(q, contexts, history=history)

            data["question"].append(q)
            data["answer"].append(answer)
            data["contexts"].append(contexts)
            data["retrieved_ids"].append(retrieved_ids)
            data["ground_truth"].append(gt)
            data["expected_contexts"].append(item.get("expected_contexts", []))
            data["expected_chunks"].append(item.get("expected_chunks", []))

        eval_service = RagasEvalService(judge_engine=get_container().inference_engine())

        faith_scores = []
        relevance_scores = []
        precision_scores = []
        recall_scores = []
        det_recalls = []
        det_precisions = []

        for i in range(len(data["question"])):
            q = data["question"][i]
            a = data["answer"][i]
            c_str = "\n".join(data["contexts"][i])
            gt = data["ground_truth"][i]

            # Deterministic Metrics
            det_metrics = self.calculate_deterministic_metrics(
                retrieved_contexts=data["contexts"][i],
                retrieved_ids=data["retrieved_ids"][i],
                expected_contexts=data["expected_contexts"][i],
                expected_chunks=data["expected_chunks"][i],
            )
            det_recalls.append(det_metrics["deterministic_context_recall"])
            det_precisions.append(det_metrics["deterministic_context_precision"])

            prompt = f"""
            Évalue l'interaction RAG ci-dessous en la comparant à la Vérité Terrain (Ground Truth) attendue :
            
            Question de l'utilisateur :
            {q}
            
            Contexte de connaissances fourni :
            {c_str}
            
            Réponse générée par le système :
            {a}
            
            Vérité Terrain attendue (Ground Truth) :
            {gt}
            """

            try:
                res_obj = eval_service.judge_engine.generate_structured(
                    prompt=prompt,
                    response_model=EvaluationResult,
                    system_prompt="Tu es un juge sémantique d'IA impartial chargé de mesurer la qualité d'une interaction RAG.",
                )
                faith_scores.append(res_obj.faithfulness)
                relevance_scores.append(res_obj.answer_relevancy)
                precision_scores.append(res_obj.context_precision)
                recall_scores.append(
                    res_obj.context_recall
                    if res_obj.context_recall is not None
                    else 0.0
                )
            except Exception as e:
                logger.error(f"Error judging row in eval_ragas: {e}")
                faith_scores.append(0.0)
                relevance_scores.append(0.0)
                precision_scores.append(0.0)
                recall_scores.append(0.0)

        result = {
            "faithfulness": (
                sum(faith_scores) / len(faith_scores) if faith_scores else 0.0
            ),
            "answer_relevancy": (
                sum(relevance_scores) / len(relevance_scores)
                if relevance_scores
                else 0.0
            ),
            "context_precision": (
                sum(precision_scores) / len(precision_scores)
                if precision_scores
                else 0.0
            ),
            "context_recall": (
                sum(recall_scores) / len(recall_scores) if recall_scores else 0.0
            ),
            "deterministic_context_recall": (
                sum(det_recalls) / len(det_recalls) if det_recalls else 0.0
            ),
            "deterministic_context_precision": (
                sum(det_precisions) / len(det_precisions) if det_precisions else 0.0
            ),
        }

        logger.info(f"📊 Results ({mode}):")
        logger.info(result)
        return result


if __name__ == "__main__":
    test_set = [
        {
            "question": "Qui a écrit le manga One Piece ?",
            "ground_truth": "Eiichiro Oda",
        },
        {
            "question": "Quels sont les thèmes principaux de Naruto ?",
            "ground_truth": "Ninja, Action, Aventure, Shonen",
        },
    ]

    evaluator = RAGEvaluator()

    async def compare():
        # Évaluation Vector-only
        await evaluator.run_evaluation(test_set, mode="vector")
        # Évaluation Hybrid
        await evaluator.run_evaluation(test_set, mode="hybrid")

    asyncio.run(compare())
