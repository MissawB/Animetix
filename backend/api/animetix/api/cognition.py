import logging

from rest_framework import permissions, status
from rest_framework.views import APIView

logger = logging.getLogger("animetix.api.cognition")
from core.domain.services.berrix_economy import FEATURE_BX_COSTS  # noqa: E402
from rest_framework.response import Response  # noqa: E402

from animetix.api.billing import deduct_berrix  # noqa: E402

from ..containers import get_container  # noqa: E402
from ..models import AIFeedback, ArchetypeDriftSnapshot  # noqa: E402
from ..serializers import (  # noqa: E402
    AIDebateSerializer,
    CFRStrategySerializer,
    CounterfactualSerializer,
    CoveOracleSerializer,
)


class ArchetypeNexusView(APIView):
    """
    Interface de profilage cognitif avancé.
    Expose le drift d'archétype et les règles logiques déduites par Z3.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        container = get_container()
        drift_service = container.core.archetype_drift_service()
        profiler = container.core.neuro_symbolic_user_profiler()
        feedback_port = container.persistence.feedback_adapter()

        user = request.user
        user_id = user.id

        # 1. Calcul du Drift d'Archétype
        drift_config = drift_service.calculate_drift(user_id)

        # 2. Récupération des feedbacks pour le profiler
        feedbacks = feedback_port.get_user_feedback(user_id, limit=50)

        # 3. Déduction des règles logiques (Z3)
        logical_rules = profiler.deduce_preference_rules(feedbacks)

        # 4. Statistiques cognitives (certaines mockées, certaines calculées)
        stats = {
            "shonen_affinity": 0.85,  # Mocked for now
            "seinen_affinity": 0.42,  # Mocked for now
            "logic_consistency": 0.92,
            "memory_depth": len(feedbacks),
        }

        # 5. Enregistrement d'un Snapshot historique (si pas de snapshot récent)
        # On limite à un snapshot par heure pour éviter de polluer la DB
        import datetime  # noqa: E402

        from django.utils import timezone  # noqa: E402

        one_hour_ago = timezone.now() - datetime.timedelta(hours=1)

        recent_snapshot = ArchetypeDriftSnapshot.objects.filter(
            user=user, created_at__gt=one_hour_ago
        ).exists()
        if not recent_snapshot:
            ArchetypeDriftSnapshot.objects.create(
                user=user,
                archetype_id=drift_config.archetype_id,
                intensity=drift_config.aura_intensity,
                shonen_affinity=stats["shonen_affinity"],
                seinen_affinity=stats["seinen_affinity"],
                logic_consistency=stats["logic_consistency"],
            )

        # 6. Récupération de l'historique (pour le graph de drift)
        # On récupère les 20 derniers snapshots et on les remet dans l'ordre chronologique
        history_snapshots = list(
            ArchetypeDriftSnapshot.objects.filter(user=user).order_by("-created_at")[
                :20
            ]
        )
        history_snapshots.reverse()

        drift_history = []
        for snap in history_snapshots:
            drift_history.append(
                {
                    "date": snap.created_at.isoformat(),
                    "archetype": snap.archetype_id,
                    "intensity": snap.intensity,
                    "shonen": snap.shonen_affinity,
                    "seinen": snap.seinen_affinity,
                }
            )

        # 7. Formattage des signaux récents
        recent_signals = []
        for fb in feedbacks[:10]:
            recent_signals.append(
                {
                    "context": fb.get("input_context", ""),
                    "is_positive": fb.get("is_positive", True),
                    "timestamp": fb.get("created_at"),
                }
            )

        return Response(
            {
                "archetype": {
                    "id": drift_config.archetype_id,
                    "accent": drift_config.primary_accent,
                    "aura_type": drift_config.aura_type,
                    "intensity": drift_config.aura_intensity,
                    "font_vibe": drift_config.font_vibe,
                },
                "logical_rules": logical_rules,
                "recent_signals": recent_signals,
                "cognitive_stats": stats,
                "drift_history": drift_history,
            }
        )


class AIDebateArenaView(APIView):
    """
    Interface pour orchestrer des débats entre agents IA sur des thématiques de lore.
    Utilise le SelfPlayDebateService.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AIDebateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        container = get_container()
        debate_service = container.core.self_play_debate_service()

        # GPU (multi-agent LLM debate) → consume Berrix. Before the try so a 402
        # isn't swallowed into a 500.
        deduct_berrix(request.user, FEATURE_BX_COSTS["ai_debate"], "Debate Arena (IA)")

        try:
            record = debate_service.run_debate(**serializer.validated_data)
            return Response(record)
        except Exception:
            logger.exception("Error in self-play debate")
            return Response({"error": "Internal server error"}, status=500)


class NeuroMemoryManagementView(APIView):
    """
    Gestion fine des règles logiques déduites (Neuro-Symbolique).
    Permet à l'utilisateur de révoquer ce que l'IA a 'compris'.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        container = get_container()
        profiler = container.core.neuro_symbolic_user_profiler()
        feedback_port = container.persistence.feedback_adapter()
        user_id = request.user.id
        feedbacks = feedback_port.get_user_feedback(user_id, limit=100)

        # On passe les dictionnaires de feedbacks (incluant is_ignored et weight) au profileur
        rules = profiler.deduce_preference_rules(feedbacks)

        return Response(
            {
                "status": "success",
                "deduced_rules": [
                    {
                        "id": i,
                        "rule": r,
                        "confidence": 0.95,
                        "source": "Z3 Theorem Prover",
                    }
                    for i, r in enumerate(rules)
                ],
                "signals": feedbacks,  # On renvoie les signaux bruts pour gestion granulaire
                "total_signals": len(feedbacks),
            }
        )

    def post(self, request):
        """Révoquer une règle ou réinitialiser le profil logique."""
        action = request.data.get("action")
        feedback_id = request.data.get("feedback_id")

        if action == "reset":
            # Simulation d'un reset : on ignore tous les feedbacks de l'utilisateur
            AIFeedback.objects.filter(user=request.user).update(is_ignored=True)
            return Response(
                {"status": "success", "message": "Neuro-Symbolic profile reset."}
            )

        if action == "revoke":
            if not feedback_id:
                return Response({"error": "feedback_id is required"}, status=400)
            AIFeedback.objects.filter(id=feedback_id, user=request.user).update(
                is_ignored=True
            )
            return Response({"status": "success", "message": "Signal revoked."})

        if action == "restore":
            if not feedback_id:
                return Response({"error": "feedback_id is required"}, status=400)
            AIFeedback.objects.filter(id=feedback_id, user=request.user).update(
                is_ignored=True
            )  # Wait, restore should set False
            AIFeedback.objects.filter(id=feedback_id, user=request.user).update(
                is_ignored=False
            )
            return Response({"status": "success", "message": "Signal restored."})

        if action == "update_weight":
            weight = request.data.get("weight")
            if not feedback_id or weight is None:
                return Response(
                    {"error": "feedback_id and weight are required"}, status=400
                )
            AIFeedback.objects.filter(id=feedback_id, user=request.user).update(
                weight=weight
            )
            return Response({"status": "success", "message": "Weight updated."})

        return Response({"error": "Invalid action"}, status=400)


class CounterfactualSimulatorView(APIView):
    """
    Simulateur de timelines alternatives pour une conversation donnée.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CounterfactualSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        container = get_container()
        simulator = container.core.counterfactual_simulator()

        # GPU (LLM counterfactual generation) → consume Berrix (before the try).
        deduct_berrix(
            request.user,
            FEATURE_BX_COSTS["counterfactual"],
            "Counterfactual Simulator (IA)",
        )

        try:
            result = simulator.simulate_counterfactual_path(
                actual_dialogue=serializer.validated_data["actual_context"],
                what_if_query=serializer.validated_data["what_if"],
            )
            return Response(result)
        except Exception:
            logger.exception("Error in counterfactual simulation")
            return Response({"error": "Internal server error"}, status=500)


class CoveOracleView(APIView):
    """
    Interface pour visualiser le processus Chain-of-Verification (CoVe).
    Réduit les hallucinations en décomposant et vérifiant les assertions.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CoveOracleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        container = get_container()
        cove_service = container.core.cove_oracle_service()

        # GPU (chain-of-verification LLM calls) → consume Berrix (before the try).
        deduct_berrix(request.user, FEATURE_BX_COSTS["cove_oracle"], "CoVe Oracle (IA)")

        try:
            trace = cove_service.trace_verification(**serializer.validated_data)
            return Response(trace)
        except Exception:
            logger.exception("CoVe Error")
            return Response({"error": "Internal server error"}, status=500)


class CFRStrategyLabView(APIView):
    """
    Interface pour visualiser la convergence du solveur CFR (Counterfactual Regret Minimization).
    Simule la résolution de dilemmes stratégiques pour Akinetix.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CFRStrategySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        container = get_container()
        cfr_solver = container.core.cfr_game_solver()

        try:
            result = cfr_solver.solve_with_history(**serializer.validated_data)
            return Response(result)
        except Exception:
            logger.exception("CFR Simulation Error")
            return Response({"error": "Internal server error"}, status=500)
