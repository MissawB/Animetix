from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from dependency_injector.wiring import inject, Provide
from ..models import AIREvalResult, GoldDatasetEntry, AIFeedback
from ..serializers import AIREvalResultSerializer, GoldDatasetEntrySerializer, AIFeedbackSerializer
from core.ports.feedback_port import FeedbackRepositoryPort
from core.ports.eval_port import EvalResultPort
from core.ports.repository_port import RepositoryPort
from core.ports.gold_dataset_port import GoldDatasetPort
from ..containers import Container

class AIREvaluationViewSet(viewsets.ReadOnlyModelViewSet):
    """API for AI Evaluation results and stats."""
    queryset = AIREvalResult.objects.all().order_by('-created_at')
    serializer_class = AIREvalResultSerializer
    permission_classes = [permissions.IsAdminUser]

    @inject
    def __init__(self, *args, eval_port: EvalResultPort = Provide[Container.eval_adapter], **kwargs):
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
    def __init__(self, repository: RepositoryPort = Provide[Container.repository], **kwargs):
        super().__init__(**kwargs)
        self.repository = repository

    def get(self, request):
        media = request.GET.get('media', 'anime').lower()
        vibe_type = request.GET.get('type', 'thematic').lower()
        
        data = self.repository.load_latent_space(media, vibe_type)
        
        if data:
            return Response(data)
        
        return Response({"error": "Data not found"}, status=status.HTTP_404_NOT_FOUND)

class AIFeedbackAPIView(APIView):
    """API for submitting AI feedback."""
    permission_classes = [permissions.AllowAny]

    @inject
    def __init__(self, feedback_port: FeedbackRepositoryPort = Provide[Container.feedback_adapter], **kwargs):
        super().__init__(**kwargs)
        self.feedback_port = feedback_port

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
    def __init__(self, *args, gold_port: GoldDatasetPort = Provide[Container.gold_dataset_adapter], **kwargs):
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

class DPOCurationViewSet(viewsets.ViewSet):
    """API for DPO Curation and Prompt Optimization."""
    permission_classes = [permissions.IsAdminUser]

    @inject
    def __init__(self, *args, dpo_loop: DPOFeedbackLoop = Provide[Container.dpo_feedback_loop], **kwargs):
        super().__init__(*args, **kwargs)
        self.dpo_loop = dpo_loop

    @action(detail=False, methods=['post'])
    def optimize_prompt(self, request):
        prompt_key = request.data.get('prompt_key')
        if not prompt_key:
            return Response({'error': 'prompt_key is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        limit = int(request.data.get('limit', 20))
        new_prompt = self.dpo_loop.optimize_prompt_from_feedback(prompt_key, limit=limit)
        
        if new_prompt:
            return Response({
                'status': 'success', 
                'prompt_key': prompt_key,
                'optimized_system_prompt': new_prompt
            })
        
        return Response({'error': 'Optimization failed or not enough feedback'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def rejected_samples(self, request):
        limit = int(request.GET.get('limit', 50))
        samples = self.dpo_loop.get_rejected_for_curation(limit=limit)
        return Response(samples)
