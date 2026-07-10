"""Spatial-computing labs: image/video to 3D reconstruction."""

from animetix_project.logging_config import get_logger
from dependency_injector.wiring import Provide, inject  # noqa: E402
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from ...containers import Container  # noqa: E402

logger = get_logger("animetix." + __name__)

from core.domain.services.berrix_economy import FEATURE_BX_COSTS  # noqa: E402

from animetix.api.billing import deduct_berrix  # noqa: E402


class SpatialLabDataView(APIView):
    """Métadonnées pour les outils de Calcul Spatial."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(
            {
                "status": "active",
                "tools": [
                    {
                        "id": "generate-3d",
                        "name": "Image-to-3D",
                        "description": "Generate a navigable 3D scene from a single image (Gaussian Splatting).",
                        "endpoint": "/api/v1/labs/spatial/generate-3d/",
                    },
                    {
                        "id": "cinematic",
                        "name": "Cinematic Reconstruction",
                        "description": "Reconstruct dynamic volumetric 3D scenes from video clips.",
                        "endpoint": "/api/v1/labs/spatial/cinematic/",
                    },
                ],
            }
        )


class Generate3DDataView(APIView):
    """Génère une scène 3D (PLY) à partir d'une image."""

    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(
        self,
        spatial_service=Provide[Container.core.spatial_computing_service],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.spatial_service = spatial_service

    def post(self, request):
        image_file = request.FILES.get("image")
        title = request.data.get("title", "Poster 3D")

        if not image_file:
            return Response({"error": "Image file is required."}, status=400)

        # Déduction des Berrix (150 Bx pour reconstruction 3D Gaussian Splatting)
        deduct_berrix(
            request.user, FEATURE_BX_COSTS["image_to_3d"], f"Image-to-3D: {title}"
        )

        try:
            image_bytes = image_file.read()
            result = self.spatial_service.reconstruct_3d_scene(image_bytes, title)
            return Response(result)
        except Exception:
            logger.exception("Error in Generate3DDataView")
            return Response({"error": "Internal server error"}, status=500)


class CinematicReconstructionView(APIView):
    """Génère une séquence de scènes 3D à partir d'une vidéo."""

    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(
        self,
        cinematic_service=Provide[
            Container.core.cinematic_volumetric_reconstruction_service
        ],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.cinematic_service = cinematic_service

    def post(self, request):
        video_file = request.FILES.get("video")
        title = request.data.get("title", "Cinematic 3D")

        if not video_file:
            return Response({"error": "Video file is required."}, status=400)

        # Déduction des Berrix (500 Bx pour reconstruction volumétrique dynamique)
        deduct_berrix(
            request.user,
            FEATURE_BX_COSTS["cinematic_3d"],
            f"Cinematic 3D Reconstruction: {title}",
        )

        try:
            video_bytes = video_file.read()
            result = self.cinematic_service.reconstruct_dynamic_cinematic_scene(
                video_bytes, title
            )
            return Response(result)
        except Exception:
            logger.exception("Error in CinematicReconstructionView")
            return Response({"error": "Internal server error"}, status=500)
