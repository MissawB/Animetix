import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("animetix.observability")


class ObservabilityService:
    """Monitoring léger des performances IA (latence, qualité RAG, erreurs).

    Historiquement branché sur Weights & Biases, mais l'``wandb.init()`` au
    démarrage bloquait le process sur un appel réseau (le serveur ne démarrait
    plus sans ``WANDB_MODE=disabled``) pour un intérêt nul en dev. Le suivi
    runtime se fait désormais **en local** (historique de latence en mémoire +
    logs structurés) — aucune dépendance réseau. Les métriques offline restent
    couvertes par les pipelines d'évaluation dédiés
    (``pipeline/mlops/evaluation_metrics.py``).
    """

    def __init__(self, project_name: str = "animetix-prod"):
        self.project_name = project_name
        # Suivi de la latence en mémoire pour les alertes temps réel (AlertService).
        self._recent_latencies: list[float] = []
        self._max_history = 50

    def log_inference(
        self,
        model_id: str,
        latency: float,
        tokens: int,
        metadata: Optional[Dict] = None,
    ):
        """Logue les métriques d'une inférence LLM."""
        tps = tokens / latency if latency > 0 else 0
        logger.debug(
            "inference model=%s latency=%.3fs tokens=%d tps=%.1f%s",
            model_id,
            latency,
            tokens,
            tps,
            f" meta={metadata}" if metadata else "",
        )

    def log_rag_quality(
        self, query: str, similarity_score: float, faithfulness: float = 0.0
    ):
        """Logue la qualité des résultats du RAG."""
        logger.debug(
            "rag_quality similarity=%.3f faithfulness=%.3f q_len=%d",
            similarity_score,
            faithfulness,
            len(query),
        )

    def log_rag_latency(
        self, latency: float, query: str, user_id: Optional[str] = None
    ):
        """Logue la latence globale d'une requête RAG + met à jour l'historique."""
        logger.info(
            f"⏱️ RAG Latency: {latency:.2f}s for query '{query[:50]}' by user {user_id}"
        )
        self._recent_latencies.append(latency)
        if len(self._recent_latencies) > self._max_history:
            self._recent_latencies.pop(0)

    def get_average_rag_latency(self) -> float:
        """Retourne la latence moyenne des dernières requêtes RAG."""
        if not self._recent_latencies:
            return 0.0
        return sum(self._recent_latencies) / len(self._recent_latencies)

    def log_dynamic_eval(self, query: str, context: str, answer: str, evaluation: Any):
        """Logue une évaluation dynamique 'LLM-as-a-Judge'."""
        logger.debug(
            "eval faithfulness=%.3f relevancy=%.3f hallucination=%s q='%s'",
            getattr(evaluation, "faithfulness_score", 0.0),
            getattr(evaluation, "relevancy_score", 0.0),
            bool(getattr(evaluation, "hallucination_detected", False)),
            query[:100],
        )

    def log_error(self, error_type: str, message: str):
        """Logue une erreur critique de l'infrastructure IA."""
        logger.error("infra_error type=%s message=%s", error_type, message)

    def finish(self):
        """No-op conservé pour compatibilité (plus de run W&B à clôturer)."""
        return None
