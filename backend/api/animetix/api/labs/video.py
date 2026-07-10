"""Video labs: style transfer (FateZero) and Video-RAG indexing/search."""

from animetix_project.logging_config import get_logger
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from ...containers import get_container  # noqa: E402

logger = get_logger("animetix." + __name__)

from core.domain.services.berrix_economy import FEATURE_BX_COSTS  # noqa: E402

from animetix.api.billing import deduct_berrix  # noqa: E402


class VideoFateZeroLabView(APIView):
    """Transforme une vidéo avec transfert de style SOTA (FateZero)."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "gpu"
    throttle_classes = [ScopedRateThrottle]

    def post(self, request):
        container = get_container()
        video_file = request.FILES.get("video")
        studio_style = request.data.get("studio_style", "Ufotable")

        if not video_file:
            return Response({"error": "Video file is required."}, status=400)

        # Déduction des Berrix (500 Bx pour transfert de style vidéo - Très lourd)
        deduct_berrix(
            request.user,
            FEATURE_BX_COSTS["style_transfer"],
            f"FateZero Style Transfer: {studio_style}",
        )

        try:
            video_bytes = video_file.read()
            service = container.core.studio_transform_service()

            result_url = service.transform_video_to_anime_sota(
                video_bytes, studio_style
            )

            return Response(
                {
                    "status": "success",
                    "video_url": result_url,
                    "message": f"Transformation {studio_style} (FateZero) réussie.",
                }
            )
        except Exception:
            logger.exception("Error in VideoFateZeroLabView")
            return Response({"error": "Internal server error"}, status=500)


class VideoRAGIndexView(APIView):
    """Endpoint pour indexer une vidéo dans le Video-RAG."""

    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        video_file = request.FILES.get("video")
        video_id = request.data.get("video_id")

        if not video_file or not video_id:
            return Response({"error": "video and video_id are required"}, status=400)

        container = get_container()
        video_rag = container.agentic.video_rag_service()

        try:
            video_data = video_file.read()
            count = video_rag.index_video(video_id, video_data)
            return Response({"status": "success", "indexed_segments": count})
        except Exception:
            logger.exception("VideoRAGIndex Error")
            return Response({"error": "Internal server error"}, status=500)


class VideoRAGSearchView(APIView):
    """Endpoint pour rechercher des moments précis dans les vidéos indexées.

    GPU/RAG : requiert login + consomme des Berrix (règle « GPU = Bx »).
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "gpu"
    throttle_classes = [ScopedRateThrottle]

    def get(self, request):
        query = request.GET.get("q")
        if not query:
            return Response({"error": "query q is required"}, status=400)

        container = get_container()
        usage_port = container.infrastructure.usage_port()
        tier = getattr(request, "user_tier", "free")
        if not usage_port.check_quota(request.user.id, tier):
            return Response({"error": "Daily AI quota exceeded."}, status=403)
        deduct_berrix(
            request.user, FEATURE_BX_COSTS["video_rag"], "VideoRAG — recherche vidéo"
        )

        video_rag = container.agentic.video_rag_service()
        try:
            results = video_rag.search_video_segment(query, limit=10)
            usage_port.log_usage(engine="video-rag", units=1, user_id=request.user.id)
            return Response({"status": "success", "results": results})
        except Exception:
            logger.exception("VideoRAGSearch Error")
            return Response({"error": "Internal server error"}, status=500)


class VideoLabDataView(APIView):
    """Métadonnées pour les outils du Video Lab."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(
            {
                "status": "active",
                "tools": [
                    {
                        "id": "fatezero",
                        "name": "FateZero Style Transfer",
                        "description": "Temporally consistent anime style transfer for real videos.",
                        "endpoint": "/api/v1/labs/video/fatezero/",
                        "supported_styles": ["Shaft", "Ufotable", "Kyoto", "Ghibli"],
                    },
                    {
                        "id": "video-rag",
                        "name": "Video-RAG Search",
                        "description": "Semantic search for precise moments in anime videos.",
                        "endpoint": "/api/v1/labs/video/search/",
                    },
                ],
            }
        )
