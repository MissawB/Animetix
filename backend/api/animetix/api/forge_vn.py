from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from ..models import CreativeFusion
from ..containers import get_container
from animetix_project.logging_config import get_logger

logger = get_logger('animetix.api.vn')

class ForgeVNView(APIView):
    """
    API for managing Visual Novel scripts associated with Creative Fusions.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

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
                vn_service = get_container().visual_novel_service()
                script = vn_service.generate_script(fusion_id)
                if script:
                    # Conversion Pydantic -> Dict pour stockage JSONField
                    fusion.vn_script = script.model_dump()
                    fusion.save()
                    return Response({"vn_script": fusion.vn_script})
                return Response({"error": "Generation failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            elif action == 'update':
                new_script = request.data.get('vn_script')
                if new_script is None:
                    return Response({"error": "vn_script is required"}, status=status.HTTP_400_BAD_REQUEST)
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
