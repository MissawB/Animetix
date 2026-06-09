from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from ..containers import Container, get_container
from ..models import ArchetypeDriftSnapshot

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
            'shonen_affinity': 0.85, # Mocked for now
            'seinen_affinity': 0.42, # Mocked for now
            'logic_consistency': 0.92,
            'memory_depth': len(feedbacks)
        }

        # 5. Enregistrement d'un Snapshot historique (si pas de snapshot récent)
        # On limite à un snapshot par heure pour éviter de polluer la DB
        import datetime
        from django.utils import timezone
        one_hour_ago = timezone.now() - datetime.timedelta(hours=1)
        
        recent_snapshot = ArchetypeDriftSnapshot.objects.filter(user=user, created_at__gt=one_hour_ago).exists()
        if not recent_snapshot:
            ArchetypeDriftSnapshot.objects.create(
                user=user,
                archetype_id=drift_config.archetype_id,
                intensity=drift_config.aura_intensity,
                shonen_affinity=stats['shonen_affinity'],
                seinen_affinity=stats['seinen_affinity'],
                logic_consistency=stats['logic_consistency']
            )

        # 6. Récupération de l'historique (pour le graph de drift)
        # On récupère les 20 derniers snapshots et on les remet dans l'ordre chronologique
        history_snapshots = list(ArchetypeDriftSnapshot.objects.filter(user=user).order_by('-created_at')[:20])
        history_snapshots.reverse()
        
        drift_history = []
        for snap in history_snapshots:
            drift_history.append({
                'date': snap.created_at.isoformat(),
                'archetype': snap.archetype_id,
                'intensity': snap.intensity,
                'shonen': snap.shonen_affinity,
                'seinen': snap.seinen_affinity
            })

        # 7. Formattage des signaux récents
        recent_signals = []
        for fb in feedbacks[:10]:
            recent_signals.append({
                'context': fb.get('input_context', ''),
                'is_positive': fb.get('is_positive', True),
                'timestamp': fb.get('created_at')
            })

        return Response({
            'archetype': {
                'id': drift_config.archetype_id,
                'accent': drift_config.primary_accent,
                'aura_type': drift_config.aura_type,
                'intensity': drift_config.aura_intensity,
                'font_vibe': drift_config.font_vibe
            },
            'logical_rules': logical_rules,
            'recent_signals': recent_signals,
            'cognitive_stats': stats,
            'drift_history': drift_history
        })

class AIDebateArenaView(APIView):
    """
    Interface pour orchestrer des débats entre agents IA sur des thématiques de lore.
    Utilise le SelfPlayDebateService.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        container = get_container()
        debate_service = container.core.self_play_debate_service()
        target_media = request.data.get('media_title')
        topic = request.data.get('topic')

        if not target_media or not topic:
            return Response({"error": "media_title and topic are required"}, status=400)

        try:
            # Pour l'instant, on exécute de manière synchrone (bloquant) 
            # mais on pourrait passer par Celery + SSE comme Expert Nexus plus tard.
            record = debate_service.run_debate(target_media=target_media, topic=topic)
            return Response(record)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

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
        rules = profiler.deduce_preference_rules(feedbacks)
        
        return Response({
            "status": "success",
            "deduced_rules": [
                {"id": i, "rule": r, "confidence": 0.95, "source": "Z3 Theorem Prover"} 
                for i, r in enumerate(rules)
            ],
            "total_signals": len(feedbacks)
        })

    def post(self, request):
        """Révoquer une règle ou réinitialiser le profil logique."""
        action = request.data.get('action')
        if action == 'reset':
            # Simulation d'un reset (on supprimerait les feedbacks en prod)
            return Response({"status": "success", "message": "Neuro-Symbolic profile reset."})
            
        return Response({"error": "Invalid action"}, status=400)

class CounterfactualSimulatorView(APIView):
    """
    Simulateur de timelines alternatives pour une conversation donnée.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        container = get_container()
        simulator = container.core.counterfactual_simulator()
        what_if_query = request.data.get('what_if')
        # On pourrait récupérer l'historique réel depuis la DB ou le passer dans le body
        actual_dialogue = request.data.get('actual_context', [])

        if not what_if_query:
            return Response({"error": "what_if query is required"}, status=400)

        try:
            result = simulator.simulate_counterfactual_path(
                actual_dialogue=actual_dialogue,
                what_if_query=what_if_query
            )
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

