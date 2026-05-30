import random
from animetix_project.logging_config import get_logger
from celery.result import AsyncResult
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from dependency_injector.wiring import inject, Provide
from ...containers import Container
from animetix.api.dependencies import get_session_service
from ...models import CreativeFusion
from core.domain.services.guardrail_service import GuardrailService
from core.ports.usage_port import UsagePort

logger = get_logger("animetix." + __name__)

# --- ARCHETYPIST / CREATIVE FUSION ---

class ArchetypistStartFusionView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @inject
    def post(self, request, 
             catalog_service = Provide[Container.core.catalog_service],
             guardrail_service: GuardrailService = Provide[Container.core.guardrail_service],
             usage_port: UsagePort = Provide[Container.infrastructure.usage_port]):
        session_service = get_session_service(request)
        port = session_service.port
        media_type = port.get('media_type', 'Anime')

        # Quota Check
        tier = getattr(request, 'user_tier', 'free')
        if not usage_port.check_quota(request.user.id, tier):
             return Response({"error": "Daily AI quota exceeded."}, status=status.HTTP_403_FORBIDDEN)
        
        title_A = request.data.get('title_A')
        title_B = request.data.get('title_B')
        media_A = request.data.get('media_type_A', media_type)
        media_B = request.data.get('media_type_B', media_type)
        
        chaos_level = int(request.data.get('chaos_level', 50))
        universe_balance = int(request.data.get('universe_balance', 50))
        art_style = request.data.get('art_style', 'Cyberpunk')
        parent_id = request.data.get('parent_id')

        # 1. Guardrail Check on Art Style and Titles
        check_text = f"Titles: {title_A or ''} x {title_B or ''}. Style: {art_style}"
        guard_input = guardrail_service.validate_input(check_text)
        if not guard_input.get("is_safe", True):
            return Response(
                {"error": f"Security violation: {guard_input.get('reason')}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = catalog_service.load_data(media_type)
        data_A = catalog_service.load_data(media_A) if media_A != media_type else data
        data_B = catalog_service.load_data(media_B) if media_B != media_type else data
        
        if not data_A or not data_B:
            return Response({"error": "Catalog data missing"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        valid_A = [t for t in data_A.get('titles', []) if t in data_A.get('title_to_full_data', {})]
        valid_B = [t for t in data_B.get('titles', []) if t in data_B.get('title_to_full_data', {})]
        
        t1 = title_A if title_A else random.choice(valid_A[:500])
        t2 = title_B if title_B else random.choice(valid_B[:500])
        
        item1 = data_A['title_to_full_data'].get(t1)
        item2 = data_B['title_to_full_data'].get(t2)
        
        if not item1 or not item2:
            return Response({"error": "Items not found"}, status=status.HTTP_404_NOT_FOUND)
            
        parent_fusion = None
        if parent_id:
            try:
                parent_fusion = CreativeFusion.objects.get(id=parent_id)
            except (CreativeFusion.DoesNotExist, ValueError) as e:
                logger.warning(f"Handled error in ArchetypistStartFusionView: {e}")
                
        fusion = CreativeFusion.objects.create(
            title_a=t1, title_b=t2, media_type_a=media_A, media_type_b=media_B,
            chaos_level=chaos_level, universe_balance=universe_balance, art_style=art_style,
            creator=request.user if request.user.is_authenticated else None,
            parent=parent_fusion,
            scenario_text="Génération en cours..."
        )
        
        from ...tasks import generate_fusion_scenario_task, generate_fusion_image_task
        from celery import chain
        
        language = port.get('language', 'Français')
        
        task = chain(
            generate_fusion_scenario_task.s(
                media_type, item1, item2, 
                language, 
                chaos_level=chaos_level, universe_balance=universe_balance, art_style=art_style
            ), 
            generate_fusion_image_task.s(item1, item2, art_style=art_style)
        ).delay()

        # Log Usage (Heavy task trigger)
        usage_port.log_usage(engine="archetypist-fusion-engine", units=30, user_id=request.user.id)
        
        return Response({
            'fusion_id': fusion.id,
            'task_id': task.id,
            'title_a': t1,
            'title_b': t2,
            'item_a_image': item1.get('image'),
            'item_b_image': item2.get('image')
        })

class ArchetypistTaskStatusView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        task_id = request.query_params.get('task_id')
        fusion_id = request.query_params.get('fusion_id')
        
        if not task_id or not fusion_id:
            return Response({"error": "task_id and fusion_id required"}, status=status.HTTP_400_BAD_REQUEST)
            
        task = AsyncResult(task_id)
        status_msg = "En cours..."
        
        if task.state == 'PENDING':
            status_msg = "En attente de traitement..."
        elif task.state != 'FAILURE':
            if task.info and isinstance(task.info, dict):
                status_msg = task.info.get('status', status_msg)
                
        response_data = {
            'state': task.state,
            'status': status_msg
        }
        
        if task.ready():
            try:
                fusion = CreativeFusion.objects.get(id=fusion_id)
                response_data['scenario'] = fusion.scenario_text
                response_data['image_url'] = fusion.image_url
                response_data['completed'] = True
            except CreativeFusion.DoesNotExist:
                return Response({"error": "Fusion not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            response_data['completed'] = False
            
        return Response(response_data)
