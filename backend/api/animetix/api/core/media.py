"""Media search, detail and the signed external-image proxy."""

import base64
import hashlib

from animetix_project.logging_config import get_logger
from core.constants import ALLOWED_IMAGE_MIMES, MAX_IMAGE_SIZE  # noqa: E402
from core.domain.services.berrix_economy import FEATURE_BX_COSTS
from core.domain.services.guardrail_service import GuardrailService
from core.ports.usage_port import UsagePort
from core.utils.security import (
    safe_http_request,
    validate_file_mime_type,
    validate_file_size,
    verify_proxy_signature,
)
from dependency_injector.wiring import Provide, inject
from django.core.cache import cache  # noqa: E402
from django.http import HttpResponse  # noqa: E402
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit  # noqa: E402
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from animetix.api.billing import deduct_berrix

from ...containers import Container
from ...serializers import MediaItemSerializer

logger = get_logger("animetix.api")


@ratelimit(key="ip", rate="30/m", method="GET", block=True)
def image_proxy_view(request):
    """
    Proxy pour les images externes avec cache local.
    Sécurisé par signature HMAC, Rate Limiting et validation binaire.
    """
    encoded_url = request.GET.get("url")
    signature = request.GET.get("sig")

    if not encoded_url or not signature:
        return HttpResponse("Missing parameters", status=400)

    try:
        url = base64.b64decode(encoded_url).decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to decode image proxy URL: {e}")
        return HttpResponse(status=400)

    # 1. Vérification de la signature cryptographique (Prévention Open Proxy)
    if not verify_proxy_signature(url, signature):
        logger.warning(f"🚩 Invalid proxy signature detected for URL: {url}")
        return HttpResponse("Forbidden: Invalid signature", status=403)

    cache_key = (
        f"img_cache_{hashlib.md5(url.encode(), usedforsecurity=False).hexdigest()}"
    )
    cached_data = cache.get(cache_key)

    if cached_data:
        return HttpResponse(
            cached_data["content"], content_type=cached_data["content_type"]
        )

    try:
        # safe_http_request gère la validation DNS et les sauts de redirection en toute sécurité
        response = safe_http_request("GET", url, timeout=10)

        if response.status_code == 200:
            content = response.content

            # 2. Validation de la taille (DoS Protection)
            if not validate_file_size(len(content), MAX_IMAGE_SIZE):
                return HttpResponse("Entity Too Large", status=413)

            # 3. Validation du type MIME réel (Magic Number)
            if not validate_file_mime_type(content, ALLOWED_IMAGE_MIMES):
                logger.warning(f"🚩 Non-image content detected in proxy for URL: {url}")
                return HttpResponse("Forbidden: Content type not allowed", status=403)

            content_type = response.headers.get("Content-Type", "image/jpeg")
            cache.set(
                cache_key,
                {"content": content, "content_type": content_type},
                60 * 60 * 24 * 7,
            )
            return HttpResponse(content, content_type=content_type)

    except ValueError as ve:
        logger.warning(f"Blocked unsafe request in image proxy: {ve}")
        return HttpResponse("Forbidden: Unsafe request detected", status=403)
    except Exception as e:
        logger.error("Image Proxy Error: %s", e, exc_info=True)

    return HttpResponse(status=404)


@method_decorator(
    ratelimit(key="ip", rate="20/m", method="GET", block=True), name="dispatch"
)
@method_decorator(
    ratelimit(key="user", rate="5/m", method="POST", block=True), name="dispatch"
)
class MediaSearchView(APIView):
    """Recherche d'œuvres via SQL ou Multi-Modale (CLIP)."""

    permission_classes = [permissions.AllowAny]

    @inject
    def __init__(
        self,
        guardrail_service: GuardrailService = Provide[Container.core.guardrail_service],
        usage_port: UsagePort = Provide[Container.infrastructure.usage_port],
        catalog_service=Provide[Container.core.catalog_service],
        cross_modal_search_service=Provide[Container.core.cross_modal_search_service],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.guardrail_service = guardrail_service
        self.usage_port = usage_port
        self.catalog_service = catalog_service
        self.cross_modal_search_service = cross_modal_search_service

    def get(self, request):
        media_type = request.query_params.get("media_type")
        query = request.query_params.get("q", "")
        limit = min(int(request.query_params.get("limit", 10)), 50)

        if not query and not media_type:
            return Response([])

        # Input Guardrail (Anti-Jailbreak, Injection)
        if query:
            guard_input = self.guardrail_service.validate_input(
                query, allow_llm=request.user.is_authenticated
            )
            if not guard_input.get("is_safe", True):
                return Response(
                    {"error": guard_input.get("reason", "Inappropriate search query.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        results = self.catalog_service.search_items(query, media_type, limit)
        return Response(self._format_results(results))

    def post(self, request):
        """Recherche par image (Cross-Modal). Requiert Authentification + Quota."""
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required for image search."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Quota Check
        tier = getattr(request, "user_tier", "free")
        if not self.usage_port.check_quota(request.user.id, tier):
            return Response(
                {"error": "Daily AI quota exceeded."}, status=status.HTTP_403_FORBIDDEN
            )

        image_file = request.FILES.get("image")
        request.data.get("media_type", "Anime")
        limit = min(int(request.data.get("limit", 10)), 20)

        if not image_file:
            return Response({"error": "No image provided"}, status=400)

        # Berrix deduction for the CLIP cross-modal search (raises 402 if balance
        # too low). Outside the try below so PaymentRequired isn't swallowed into 500.
        deduct_berrix(
            request.user,
            FEATURE_BX_COSTS["vision_clip"],
            "Recherche par image (CLIP)",
        )

        try:
            if not validate_file_size(image_file.size, MAX_IMAGE_SIZE):
                return Response(
                    {
                        "error": f"Image is too large (Max: {MAX_IMAGE_SIZE / 1024 / 1024}MB)"
                    },
                    status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                )

            image_data = b"".join(chunk for chunk in image_file.chunks())

            if not validate_file_mime_type(image_data, ALLOWED_IMAGE_MIMES):
                return Response(
                    {
                        "error": "Invalid image format. Allowed formats: JPEG, PNG, WEBP."
                    },
                    status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                )

            # Appel au service Cross-Modal
            results = self.cross_modal_search_service.deep_multimodal_search(
                text_query="", image_data=image_data, limit=limit
            )

            # Log Usage
            self.usage_port.log_usage(
                engine="clip-vit-large-patch14", units=1, user_id=request.user.id
            )

            return Response(self._format_results(results))
        except Exception:
            logger.exception("Error in image search")
            return Response({"error": "Internal server error"}, status=500)

    def _format_results(self, results):
        # Utilise le serializer pour formater les résultats
        serializer = MediaItemSerializer(results, many=True)
        return serializer.data


class MediaDetailView(APIView):
    """Détails complets d'une œuvre."""

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @inject
    def __init__(
        self,
        catalog_service=Provide[Container.core.catalog_service],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.catalog_service = catalog_service

    def get(self, request, media_type, item_id):
        from ...models import MediaItem  # noqa: E402
        from ...serializers import MediaItemSerializer  # noqa: E402

        # 1. Tentative via SQL direct (Source of Truth)
        try:
            item_obj = MediaItem.objects.get(media_type=media_type, external_id=item_id)
            serializer = MediaItemSerializer(item_obj)
            return Response(serializer.data)
        except MediaItem.DoesNotExist:
            logger.debug(
                f"MediaItem {item_id} ({media_type}) not found in SQL, falling back to Catalog."
            )

        # 2. Fallback via Catalog Service (si non synchronisé en SQL)
        data = self.catalog_service.load_data(media_type)
        if data:
            item = next(
                (i for i in data.get("db", []) if str(i.get("id")) == str(item_id)),
                None,
            )
            if item:
                # Enrichissement avec les nœuds du graphe si présents
                graph_nodes = item.get("graph_nodes", {})
                item["studios"] = graph_nodes.get("studios", [])
                item["author"] = graph_nodes.get("author")
                item["related_items"] = graph_nodes.get("related_items", [])

                return Response(item)

        return Response({"error": "Item not found"}, status=404)
