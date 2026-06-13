from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from dependency_injector.wiring import inject, Provide
from ..models import CreativeFusion
from ..serializers import CreativeFusionSerializer
from ..containers import Container, get_container
from core.domain.services.guardrail_service import GuardrailService
from core.ports.usage_port import UsagePort
from animetix_project.logging_config import get_logger

logger = get_logger('animetix.api.vn')

class TheaterListView(APIView):
    """
    Returns a list of all public fusions that have a generated Visual Novel script.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        fusions = CreativeFusion.objects.filter(
            vn_script__isnull=False, 
            is_public=True
        ).order_by('-created_at')
        serializer = CreativeFusionSerializer(fusions, many=True)
        return Response(serializer.data)

class ForgeVNView(APIView):
    """
    API for managing Visual Novel scripts associated with Creative Fusions.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @inject
    def __init__(self, 
                 guardrail_service: GuardrailService = Provide[Container.core.guardrail_service],
                 usage_port: UsagePort = Provide[Container.infrastructure.usage_port],
                 **kwargs):
        super().__init__(**kwargs)
        self.guardrail_service = guardrail_service
        self.usage_port = usage_port

    def get(self, request, fusion_id):
        """Returns the VN script for a specific fusion."""
        try:
            fusion = CreativeFusion.objects.get(id=fusion_id)
            
            # Sécurité : Vérifier que la fusion est publique ou que l'utilisateur en est le créateur
            if not fusion.is_public and fusion.creator != request.user and not getattr(request.user, 'is_staff', False):
                 return Response({"error": "Unauthorized access to private fusion"}, status=status.HTTP_403_FORBIDDEN)

            return Response({"vn_script": fusion.vn_script})
        except CreativeFusion.DoesNotExist:
            return Response({"error": "Fusion not found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, fusion_id):
        """
        Action 'generate': Generates a script and saves it.
        Action 'update': Updates the script (Director Mode).
        """
        action = request.data.get('action')
        try:
            fusion = CreativeFusion.objects.get(id=fusion_id)
            
            # Authorization check: only the creator can update/generate for their fusion
            if action in ['generate', 'update'] and fusion.creator != request.user:
                 return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

            if action == 'generate':
                # Déduction des Bx (100 Bx pour un script VN complet)
                from animetix.api.billing import deduct_berrix
                deduct_berrix(request.user, 100, "Génération de Script Visual Novel")

                # Guardrail check on fusion metadata
                check_text = f"{fusion.title_a} x {fusion.title_b}\n{fusion.scenario_text}"
                guard_input = self.guardrail_service.validate_input(check_text)
                if not guard_input.get("is_safe", True):
                    return Response(
                        {"error": f"Fusion content rejected by security filters: {guard_input.get('reason')}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    vn_service = get_container().core.visual_novel_service()
                    script = vn_service.generate_script(fusion_id)
                    if script:
                        # Conversion Pydantic -> Dict pour stockage JSONField
                        script_data = script.model_dump()
                        
                        # Output Guardrail (validate the whole script content)
                        guard_output = self.guardrail_service.validate_output(str(script_data))
                        if not guard_output.get("is_safe", True):
                             return Response({"error": "Generated script failed safety validation."}, status=status.HTTP_400_BAD_REQUEST)

                        fusion.vn_script = script_data
                        fusion.save()

                        # Log Usage
                        self.usage_port.log_usage(engine="vn-script-generator", units=20, user_id=request.user.id)

                        return Response({"vn_script": fusion.vn_script})
                    return Response({"error": "Generation failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                except Exception as e:
                    logger.error(f"Generation error: {e}")
                    return Response({"error": "Internal generation error"}, status=500)

            elif action == 'update':
                new_script = request.data.get('vn_script')
                if new_script is None:
                    return Response({"error": "vn_script is required"}, status=status.HTTP_400_BAD_REQUEST)
                
                # Sanitize user provided script if it's going to be shared
                guard_input = self.guardrail_service.validate_input(str(new_script))
                if not guard_input.get("is_safe", True):
                    return Response({"error": "Provided script rejected by security filters."}, status=status.HTTP_400_BAD_REQUEST)

                fusion.vn_script = new_script
                fusion.save()
                return Response({"vn_script": fusion.vn_script})

            else:
                return Response({"error": f"Unknown action: {action}"}, status=status.HTTP_400_BAD_REQUEST)

        except CreativeFusion.DoesNotExist:
            return Response({"error": "Fusion not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in ForgeVNView: {e}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
