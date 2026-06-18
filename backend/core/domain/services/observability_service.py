import os
import logging
from typing import Dict, Any, Optional
import wandb

logger = logging.getLogger("animetix.observability")


class ObservabilityService:
    """
    Gère le monitoring des performances et de la qualité IA via Weights & Biases.
    Suit la latence, la dérive sémantique et l'utilisation des modèles.
    """

    def __init__(self, project_name: str = "animetix-prod"):
        self.project_name = project_name
        self.api_key = os.getenv("WANDB_API_KEY")
        self.enabled = bool(self.api_key)
        self._run = None

        # Suivi de la latence en mémoire pour les alertes temps réel
        self._recent_latencies = []
        self._max_history = 50

        if self.enabled:
            try:
                wandb.login(key=self.api_key)
                self._run = wandb.init(
                    project=self.project_name,
                    job_type="production-monitoring",
                    resume="allow",
                )
                logger.info(
                    f"🚀 W&B Monitoring initialized for project {self.project_name}"
                )
            except Exception as e:
                logger.error(f"Failed to initialize W&B: {e}")
                self.enabled = False

    def log_inference(
        self,
        model_id: str,
        latency: float,
        tokens: int,
        metadata: Optional[Dict] = None,
    ):
        """Logue les métriques d'une inférence LLM."""
        if not self.enabled:
            return

        data = {
            "inference/latency": latency,
            "inference/tokens": tokens,
            "inference/tokens_per_sec": tokens / latency if latency > 0 else 0,
            "model_id": model_id,
        }
        if metadata:
            data.update(metadata)

        wandb.log(data)

    def log_rag_quality(
        self, query: str, similarity_score: float, faithfulness: float = 0.0
    ):
        """Logue la qualité des résultats du RAG."""
        if not self.enabled:
            return

        wandb.log(
            {
                "rag/similarity_score": similarity_score,
                "rag/faithfulness": faithfulness,
                "rag/query_length": len(query),
            }
        )

    def log_rag_latency(
        self, latency: float, query: str, user_id: Optional[str] = None
    ):
        """Logue la latence globale d'une requête RAG."""
        logger.info(
            f"⏱️ RAG Latency: {latency:.2f}s for query '{query[:50]}' by user {user_id}"
        )

        # Mise à jour de l'historique local
        self._recent_latencies.append(latency)
        if len(self._recent_latencies) > self._max_history:
            self._recent_latencies.pop(0)

        if not self.enabled:
            return

        wandb.log(
            {
                "rag/latency": latency,
                "rag/query_length": len(query),
                "rag/user_id": user_id or "anonymous",
            }
        )

    def get_average_rag_latency(self) -> float:
        """Retourne la latence moyenne des dernières requêtes RAG."""
        if not self._recent_latencies:
            return 0.0
        return sum(self._recent_latencies) / len(self._recent_latencies)

    def log_dynamic_eval(self, query: str, context: str, answer: str, evaluation: Any):
        """Logue une évaluation dynamique 'LLM-as-a-Judge'."""
        if not self.enabled:
            return
        wandb.log(
            {
                "eval/faithfulness": getattr(evaluation, "faithfulness_score", 0.0),
                "eval/relevancy": getattr(evaluation, "relevancy_score", 0.0),
                "eval/hallucination_detected": 1
                if getattr(evaluation, "hallucination_detected", False)
                else 0,
                "eval/query": query[:100],
            }
        )

    def log_error(self, error_type: str, message: str):
        """Logue une erreur critique de l'infrastructure IA."""
        if not self.enabled:
            return
        wandb.log(
            {"errors/count": 1, "errors/type": error_type, "errors/message": message}
        )

    def finish(self):
        if self._run:
            self._run.finish()
