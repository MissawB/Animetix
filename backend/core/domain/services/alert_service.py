import logging
from typing import Dict
from core.ports.notification_port import NotificationPort
from .drift_service import DriftService
from .observability_service import ObservabilityService

logger = logging.getLogger("animetix.alerts")


class AlertService:
    """
    Service centralisé pour la surveillance des métriques IA et le déclenchement d'alertes.
    Regroupe les dérives sémantiques, de connaissances et les performances (latence).
    """

    def __init__(
        self,
        notification_port: NotificationPort,
        drift_service: DriftService,
        observability_service: ObservabilityService,
    ):
        self.notification_port = notification_port
        self.drift_service = drift_service
        self.obs = observability_service

        # Seuils recalibrés (2026 Ready)
        self.KNOWLEDGE_DRIFT_THRESHOLD = (
            0.40  # Augmenté de 0.20 pour réduire les faux positifs
        )
        self.LATENCY_THRESHOLD_SEC = 5.0  # Alerte si RAG > 5s en moyenne
        self.EMBEDDING_DRIFT_P_VALUE = 0.01  # Déjà calibré dans DriftService

    def check_and_alert(self, admin_user_id: int):
        """Exécute tous les contrôles de santé et notifie l'administrateur si nécessaire."""
        logger.info("📡 AlertService: Running global health check...")

        # 1. Vérification de la dérive des embeddings
        drift_report = self.drift_service.get_drift_report()
        for collection, data in drift_report.items():
            if data.get("status") == "alert":
                self._trigger_drift_alert(admin_user_id, collection, data)

        # 2. Vérification de la latence RAG
        avg_latency = self.obs.get_average_rag_latency()
        if avg_latency > self.LATENCY_THRESHOLD_SEC:
            self._trigger_latency_alert(admin_user_id, avg_latency)

    def _trigger_drift_alert(self, user_id: int, collection: str, data: Dict):
        """Envoie une notification de dérive sémantique."""
        title = f"🚨 Alerte Dérive : {collection.upper()}"
        message = (
            f"Une dérive sémantique significative a été détectée dans la collection '{collection}'. "
            f"P-value: {data.get('p_value')}. Un ré-entraînement ou une nouvelle baseline est recommandé."
        )
        logger.warning(f"Drift Alert Triggered: {message}")
        self.notification_port.send(
            user_id=user_id,
            title=title,
            message=message,
            notification_type="alert",
            link="/admin/mlops",
        )

    def _trigger_latency_alert(self, user_id: int, latency: float):
        """Envoie une notification de dégradation de performance."""
        title = "⏳ Alerte Performance : Latence Élevée"
        message = (
            f"La latence moyenne du RAG est de {latency:.2f}s, "
            f"dépassant le seuil de {self.LATENCY_THRESHOLD_SEC}s."
        )
        logger.warning(f"Latency Alert Triggered: {message}")
        self.notification_port.send(
            user_id=user_id,
            title=title,
            message=message,
            notification_type="warning",
            link="/admin/health",
        )

    def process_knowledge_drift(self, drift_result: Dict, admin_user_id: int):
        """Traite les résultats du pipeline de dérive de connaissances (seasonal)."""
        score = drift_result.get("drift_score", 0.0)

        if score > self.KNOWLEDGE_DRIFT_THRESHOLD:
            title = "🆕 Alerte Catalogue : Saisonnalité"
            message = (
                f"Le catalogue est en retard sur la saison actuelle ({score * 100:.0f}% de manque). "
                f"Il manque {len(drift_result.get('missing_items', []))} titres populaires."
            )
            self.notification_port.send(
                user_id=admin_user_id,
                title=title,
                message=message,
                notification_type="warning",
                link="/admin/pipeline",
            )
            return True
        return False
