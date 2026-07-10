"""Public app config (incl. maintenance mode) and the transparency report."""

from animetix_project.logging_config import get_logger
from dependency_injector.wiring import Provide, inject
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from animetix.api.throttles import CpuGameThrottle

from ...containers import Container

logger = get_logger("animetix.api")

# Version publiée du modèle « Champion » (libellé déclaré : aucun registre de
# version n'est persisté en base — c'est la seule source configurable).
AI_MODEL_VERSION = "Animetix-Champion-v2.4"

# Les taux (hallucination, conformité, fiabilité) sont calculés sur une fenêtre
# glissante et masqués sous un seuil d'échantillon : sur trop peu d'évaluations,
# un pourcentage donne une fausse impression de précision.
TRANSPARENCY_WINDOW_DAYS = 30
MIN_EVAL_SAMPLE = 20


@method_decorator(ensure_csrf_cookie, name="dispatch")
class ConfigView(APIView):
    """Configuration publique de l'app (type frontend ``AppConfig``).

    Porte aussi le mode maintenance : le frontend polle cet endpoint pendant
    la maintenance pour détecter la sortie, d'où le throttle minute-seulement
    (le day-cap anonyme par défaut couperait le poll) et son exemption dans
    ``MaintenanceModeMiddleware``.
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = [CpuGameThrottle]  # 60/min, jamais le cap journalier

    def get(self, request):
        from ...models import SiteConfiguration  # noqa: E402

        site = SiteConfiguration.get_solo()
        data = {
            "version": AI_MODEL_VERSION,
            "theme": "auto",
            "language": "fr",
            "maintenance_mode": site.maintenance_mode,
            "maintenance_message": site.maintenance_message,
            "maintenance_until": (
                site.maintenance_until.isoformat() if site.maintenance_until else None
            ),
            "user": {
                "is_authenticated": request.user.is_authenticated,
                "username": (
                    request.user.username if request.user.is_authenticated else None
                ),
                "rank": getattr(request.user, "profile", None)
                and request.user.profile.rank
                or None,
            },
            "features": {
                "EXPERIMENTAL_MODES": True,
            },
        }
        return Response(data)


class CustomConfigDataView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"status": "guest", "visual_theme": "default"})
        return Response({"status": "stub"})


class TransparencyDataView(APIView):
    """
    Vue de transparence communautaire — alimentée par des données réelles.

    Chaque section est calculée à partir des tables/services existants et
    encapsulée dans un try/except : l'endpoint étant public, il ne doit jamais
    renvoyer 500. Les champs sans source réelle sont renvoyés à ``None`` (le
    front applique alors ses propres valeurs de repli).
    """

    permission_classes = [permissions.AllowAny]

    @inject
    def __init__(
        self,
        sota_benchmark_service=Provide[Container.core.sota_benchmark_service],
        drift_service=Provide[Container.core.drift_service],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.sota_benchmark_service = sota_benchmark_service
        self.drift_service = drift_service

    def get(self, request):
        from datetime import timedelta  # noqa: E402

        from django.db.models import Avg  # noqa: E402
        from django.db.models.functions import TruncMonth  # noqa: E402
        from django.utils import timezone  # noqa: E402

        from ...models import (  # noqa: E402
            AIFeedback,
            AIREvalResult,
            AISafetyEvent,
            VectorRecord,
        )

        cutoff = timezone.now() - timedelta(days=TRANSPARENCY_WINDOW_DAYS)

        # 1. Feedbacks communautaires (réel, cumulés).
        total_feedbacks = AIFeedback.objects.count()
        community_satisfaction = 0.0
        if total_feedbacks:
            positive = AIFeedback.objects.filter(is_positive=True).count()
            community_satisfaction = round(positive / total_feedbacks, 2)

        # 2. Base de connaissances vectorielle (réel).
        knowledge_nodes = VectorRecord.objects.count()

        # 3. Évaluations RAG sur la fenêtre récente. Sous MIN_EVAL_SAMPLE, on
        # renvoie None : un taux sur 3 évals n'a aucune valeur informative.
        recent_evals = AIREvalResult.objects.filter(created_at__gte=cutoff)
        recent_total = recent_evals.count()
        enough_evals = recent_total >= MIN_EVAL_SAMPLE

        hallucination_rate = None
        model_reliability = None
        if enough_evals:
            recent_halluc = recent_evals.filter(hallucination_detected=True).count()
            hallucination_rate = round(recent_halluc / recent_total, 4)
            model_reliability = round(100 * (1 - hallucination_rate), 2)

        # Timeline mensuelle de la précision (réel) — le front masque le graphe
        # tant qu'il n'y a pas au moins deux points.
        timeline = [
            {"date": row["m"].strftime("%Y-%m"), "accuracy": round(row["a"], 4)}
            for row in (
                AIREvalResult.objects.annotate(m=TruncMonth("created_at"))
                .values("m")
                .annotate(a=Avg("faithfulness"))
                .order_by("m")
            )
            if row["m"] is not None and row["a"] is not None
        ]

        # 4. Conformité sécurité sur la même fenêtre (blocages Guardrail /
        # interactions évaluées), masquée sous le même seuil.
        safety_compliance = None
        if enough_evals:
            try:
                recent_blocked = AISafetyEvent.objects.filter(
                    created_at__gte=cutoff, action__in=["block", "rewrite"]
                ).count()
                safety_compliance = round(
                    max(0.0, 1 - recent_blocked / recent_total), 4
                )
            except Exception:
                logger.warning("Transparency: safety stats unavailable", exc_info=True)

        # 5. Score éthique composite à partir des seuls signaux fiables du moment.
        ethics_parts = []
        if hallucination_rate is not None:
            ethics_parts.append(1 - hallucination_rate)
        if community_satisfaction:
            ethics_parts.append(community_satisfaction)
        if safety_compliance is not None:
            ethics_parts.append(safety_compliance)
        ethics_score = (
            round(100 * sum(ethics_parts) / len(ethics_parts), 1)
            if ethics_parts
            else None
        )

        # 6. Benchmarks SOTA (source curée canonique de l'app).
        try:
            sota_benchmarks = self.sota_benchmark_service.get_all_benchmarks()
        except Exception:
            sota_benchmarks = []
            logger.warning("Transparency: SOTA benchmarks unavailable", exc_info=True)

        # 7. Dérive des embeddings (réel — test KS ; "unknown" sans baseline).
        try:
            embedding_drift = self.drift_service.get_drift_report()
        except Exception:
            embedding_drift = {}
            logger.warning("Transparency: drift report unavailable", exc_info=True)

        # Dernière activité d'évaluation (réel), sinon None.
        last_eval = AIREvalResult.objects.order_by("-created_at").first()
        last_training = last_eval.created_at.date().isoformat() if last_eval else None

        return Response(
            {
                "status": "synchronized",
                "global_metrics": {
                    "total_feedbacks": total_feedbacks,
                    "community_satisfaction": community_satisfaction,
                    "knowledge_nodes": knowledge_nodes,
                    "model_version": AI_MODEL_VERSION,
                    "last_training": last_training,
                    "uptime": model_reliability,
                },
                "model_uptime": model_reliability,
                "evolution_timeline": timeline,
                "sota_benchmarks": sota_benchmarks,
                "embedding_drift": embedding_drift,
                "ethics_score": ethics_score,
                "ethics_audit": {
                    "safety_compliance": safety_compliance,
                    "hallucination_rate": hallucination_rate,
                },
            }
        )
