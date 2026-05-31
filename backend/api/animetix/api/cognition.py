from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from dependency_injector.wiring import inject, Provide
from ..containers import Container
from core.domain.services.archetype_drift_service import ArchetypeDriftService
from core.domain.services.neuro_symbolic_user_profiler import NeuroSymbolicUserProfiler
from core.ports.feedback_port import FeedbackRepositoryPort

from core.domain.services.self_play_debate_service import SelfPlayDebateService

class ArchetypeNexusView(APIView):
    """
    Interface de profilage cognitif avancé.
    Expose le drift d'archétype et les règles logiques déduites par Z3.
    """
    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(self, 
                 drift_service: ArchetypeDriftService = Provide[Container.core.archetype_drift_service],
                 profiler: NeuroSymbolicUserProfiler = Provide[Container.core.neuro_symbolic_user_profiler],
                 feedback_port: FeedbackRepositoryPort = Provide[Container.persistence.feedback_adapter],
                 **kwargs):
        super().__init__(**kwargs)
        self.drift_service = drift_service
        self.profiler = profiler
        self.feedback_port = feedback_port

    def get(self, request):
        user_id = request.user.id
        
        # 1. Calcul du Drift d'Archétype
        drift_config = self.drift_service.calculate_drift(user_id)
        
        # 2. Récupération des feedbacks pour le profiler
        feedbacks = self.feedback_port.get_user_feedback(user_id, limit=50)
        
        # 3. Déduction des règles logiques (Z3)
        logical_rules = self.profiler.deduce_preference_rules(feedbacks)
        
        # 4. Formattage des signaux récents pour la visualisation
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
            'cognitive_stats': {
                'shonen_affinity': 0.85, # Mocked for now, should come from deeper analysis
                'seinen_affinity': 0.42,
                'logic_consistency': 0.92,
                'memory_depth': len(feedbacks)
            }
        })

class AIDebateArenaView(APIView):
    """
    Interface pour orchestrer des débats entre agents IA sur des thématiques de lore.
    Utilise le SelfPlayDebateService.
    """
    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(self, 
                 debate_service: SelfPlayDebateService = Provide[Container.core.self_play_debate_service],
                 **kwargs):
        super().__init__(**kwargs)
        self.debate_service = debate_service

    def post(self, request):
        target_media = request.data.get('media_title')
        topic = request.data.get('topic')

        if not target_media or not topic:
            return Response({"error": "media_title and topic are required"}, status=400)

        try:
            # Pour l'instant, on exécute de manière synchrone (bloquant) 
            # mais on pourrait passer par Celery + SSE comme Expert Nexus plus tard.
            record = self.debate_service.run_debate(target_media=target_media, topic=topic)
            return Response(record)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
