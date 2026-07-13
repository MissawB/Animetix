"""Video labs: style transfer (FateZero) and Video-RAG indexing/search."""

from animetix_project.logging_config import get_logger
from dependency_injector.wiring import Provide, inject  # noqa: E402
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from ...containers import Container  # noqa: E402

logger = get_logger("animetix." + __name__)

from core.domain.services.berrix_economy import FEATURE_BX_COSTS  # noqa: E402

from animetix.api.billing import deduct_berrix  # noqa: E402


class VideoFateZeroLabView(APIView):
    """Transforme une vidéo avec transfert de style SOTA (FateZero)."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "gpu"
    throttle_classes = [ScopedRateThrottle]

    @inject
    def __init__(
        self,
        studio_transform_service=Provide[Container.core.studio_transform_service],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.studio_transform_service = studio_transform_service

    def post(self, request):
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

            result_url = self.studio_transform_service.transform_video_to_anime_sota(
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

    @inject
    def __init__(
        self,
        video_rag_service=Provide[Container.agentic.video_rag_service],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.video_rag_service = video_rag_service

    def post(self, request):
        video_file = request.FILES.get("video")
        video_id = request.data.get("video_id")

        if not video_file or not video_id:
            return Response({"error": "video and video_id are required"}, status=400)

        try:
            video_data = video_file.read()
            count = self.video_rag_service.index_video(video_id, video_data)
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

    @inject
    def __init__(
        self,
        video_rag_service=Provide[Container.agentic.video_rag_service],
        usage_port=Provide[Container.infrastructure.usage_port],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.video_rag_service = video_rag_service
        self.usage_port = usage_port

    def get(self, request):
        query = request.GET.get("q")
        if not query:
            return Response({"error": "query q is required"}, status=400)

        tier = getattr(request, "user_tier", "free")
        if not self.usage_port.check_quota(request.user.id, tier):
            return Response({"error": "Daily AI quota exceeded."}, status=403)

        # `video_temporal`'s only writer (VideoRAGIndexView) is admin-gated
        # and hidden from the UI -- for an ordinary user the collection is
        # empty and a search against it can never return a result. Check
        # BEFORE charging: paying for a search that cannot possibly succeed
        # is the bug, not the missing index itself.
        if not self.video_rag_service.is_available():
            return Response(
                {
                    "error": (
                        "Recherche vidéo indisponible : aucune vidéo n'a "
                        "encore été indexée dans le Video-RAG. Réessayez "
                        "plus tard."
                    )
                },
                status=503,
            )

        deduct_berrix(
            request.user, FEATURE_BX_COSTS["video_rag"], "VideoRAG — recherche vidéo"
        )

        try:
            results = self.video_rag_service.search_video_segment(query, limit=10)
            self.usage_port.log_usage(
                engine="video-rag", units=1, user_id=request.user.id
            )
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
