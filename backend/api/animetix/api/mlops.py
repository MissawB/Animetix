from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from dependency_injector.wiring import inject, Provide
from ..models import AIREvalResult, GoldDatasetEntry, AIFeedback
from ..serializers import AIREvalResultSerializer, GoldDatasetEntrySerializer, AIFeedbackSerializer
from core.ports.feedback_port import FeedbackRepositoryPort
from core.ports.eval_port import EvalResultPort
from core.ports.repository_port import RepositoryPort
from core.ports.gold_dataset_port import GoldDatasetPort
from ..containers import Container, get_container
import datetime

class AIREvaluationViewSet(viewsets.ReadOnlyModelViewSet):
    """API for AI Evaluation results and stats."""
    queryset = AIREvalResult.objects.all().order_by('-created_at')
    serializer_class = AIREvalResultSerializer
    permission_classes = [permissions.IsAdminUser]

    @inject
    def __init__(self, *args, eval_port: EvalResultPort = Provide[Container.persistence.eval_adapter], **kwargs):
        super().__init__(*args, **kwargs)
        self.eval_port = eval_port

    @action(detail=False, methods=['get'])
    def stats(self, request):
        stats_data = self.eval_port.get_evaluation_stats()
        return Response(stats_data)

class LatentSpaceAPIView(APIView):
    """API for retrieving latent space data for visualization."""
    permission_classes = [permissions.IsAdminUser]

    @inject
    def __init__(self, repository: RepositoryPort = Provide[Container.persistence.repository], **kwargs):
        super().__init__(**kwargs)
        self.repository = repository

    def get(self, request):
        media = request.GET.get('media', 'anime').lower()
        vibe_type = request.GET.get('type', 'thematic').lower()
        
        data = self.repository.load_latent_space(media, vibe_type)
        
        if data:
            return Response(data)
        
        return Response({"error": "Data not found"}, status=status.HTTP_404_NOT_FOUND)

@method_decorator(ratelimit(key='user_or_ip', rate='5/m', method='POST', block=True), name='dispatch')
class AIFeedbackAPIView(APIView):
    """API for submitting and retrieving AI feedback."""
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    @inject
    def __init__(self, feedback_port: FeedbackRepositoryPort = Provide[Container.persistence.feedback_adapter], **kwargs):
        super().__init__(**kwargs)
        self.feedback_port = feedback_port

    def get(self, request):
        """Récupère l'historique des feedbacks de l'utilisateur connecté."""
        feedbacks = AIFeedback.objects.filter(user=request.user).order_by('-created_at')[:100]
        serializer = AIFeedbackSerializer(feedbacks, many=True)
        return Response(serializer.data)

    def post(self, request):
        is_pos = request.data.get('is_positive') == True or request.data.get('is_positive') == 'true'
        f_type = request.data.get('type', 'general')
        context = request.data.get('input_context') or request.data.get('context') or request.data.get('query', '')
        output = request.data.get('output_text') or request.data.get('output', '')
        
        user_id = request.user.id if request.user.is_authenticated else None
        
        self.feedback_port.save_feedback(
            input_context=context,
            output_text=output,
            is_positive=is_pos,
            user_id=user_id,
            feedback_type=f_type
        )
        return Response({'status': 'success', 'message': 'Feedback submitted successfully'})

class GoldDatasetViewSet(viewsets.ModelViewSet):
    """API for Gold Dataset curation."""
    queryset = GoldDatasetEntry.objects.all().order_by('-created_at')
    serializer_class = GoldDatasetEntrySerializer
    permission_classes = [permissions.IsAdminUser]

    @inject
    def __init__(self, *args, gold_port: GoldDatasetPort = Provide[Container.persistence.gold_dataset_adapter], **kwargs):
        super().__init__(*args, **kwargs)
        self.gold_port = gold_port

    @action(detail=False, methods=['post'])
    def sync_positive_feedback(self, request):
        """Syncs all uncurated positive feedback to the gold dataset."""
        count = self.gold_port.sync_positive_feedback()
        return Response({'status': 'success', 'synced_count': count})

    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        success = self.gold_port.validate_entry(pk)
        if success:
            return Response({'status': 'validated'})
        return Response({'error': 'Entry not found'}, status=status.HTTP_404_NOT_FOUND)

from core.domain.services.dpo_feedback_loop import DPOFeedbackLoop
from core.domain.services.dspy_prompt_optimizer import DSPyPromptOptimizer

class DPOCurationView(APIView):
    """API for DPO Curation (List and Post)."""
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        container = get_container()
        dpo_loop = container.core.dpo_feedback_loop()
        limit = int(request.GET.get('limit', 50))
        samples = dpo_loop.get_rejected_for_curation(limit=limit)
        return Response(samples)

    def post(self, request):
        container = get_container()
        dpo_loop = container.core.dpo_feedback_loop()
        feedback_id = request.data.get('feedback_id')
        chosen_text = request.data.get('chosen_text')
        
        if not feedback_id or not chosen_text:
            return Response({'error': 'feedback_id and chosen_text are required'}, status=400)
            
        success = dpo_loop.curate_feedback(feedback_id, chosen_text)
        if success:
            return Response({'status': 'success', 'message': 'Feedback successfully curated.'})
        return Response({'error': 'Curation failed'}, status=500)

class DSPyOptimizerView(APIView):
    """
    Interface pour piloter l'optimisation automatique des prompts via DSPy.
    Permet de muter des templates et de sélectionner le meilleur variant.
    """
    permission_classes = [permissions.IsAdminUser]

    @inject
    def __init__(self, optimizer: DSPyPromptOptimizer = Provide[Container.core.dspy_prompt_optimizer], **kwargs):
        super().__init__(**kwargs)
        self.optimizer = optimizer

    def post(self, request):
        template = request.data.get('template')
        dataset = request.data.get('dataset', [])
        
        if not template:
            return Response({'error': 'template is required'}, status=400)
        if not dataset:
            # Fallback dataset if empty for demo
            dataset = [
                {"query": "Qui est Luffy ?", "expected": "Luffy est le protagoniste de One Piece et capitaine des Chapeaux de Paille."},
                {"query": "Quel est le pouvoir de Gojo ?", "expected": "Satoru Gojo possède l'Infini et le Sixième Œil."}
            ]

        try:
            best_template, best_score = self.optimizer.evaluate_and_select_best(template, dataset)
            # On génère aussi les mutations pour l'affichage
            mutations = self.optimizer.mutate_template(template, num_mutations=3)
            
            return Response({
                'status': 'success',
                'best_template': best_template,
                'best_score': best_score,
                'all_mutations': mutations
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)

class SOTABenchmarkListView(APIView):
    """Récupère les benchmarks SOTA (State of the Art) pour les modèles IA."""
    permission_classes = [permissions.AllowAny] # Public pour la transparence

    def get(self, request):
        container = get_container()
        service = container.core.sota_benchmark_service()
        
        benchmarks = service.get_all_benchmarks()
        best_elo = service.get_best_model("elo_score")
        best_os = service.get_open_source_best()
        
        return Response({
            "status": "success",
            "timestamp": datetime.datetime.now().isoformat(),
            "benchmarks": benchmarks,
            "top_model": best_elo,
            "best_open_source": best_os[0] if best_os else None
        })
