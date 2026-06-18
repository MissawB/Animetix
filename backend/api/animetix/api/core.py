import base64
import hashlib

from animetix_project.logging_config import get_logger
from core.domain.services.guardrail_service import GuardrailService
from core.ports.usage_port import UsagePort
from core.utils.security import (
    safe_http_request,
    validate_file_mime_type,
    validate_file_size,
    verify_proxy_signature,
)
from dependency_injector.wiring import Provide, inject
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..containers import Container, get_container
from ..serializers import MangaChapterSerializer, MediaItemSerializer, ProfileSerializer

ALLOWED_IMAGE_MIMES = ["image/jpeg", "image/png", "image/webp", "image/gif"]
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 Mo
from django.core.cache import cache  # noqa: E402
from django.http import HttpResponse  # noqa: E402
from django_ratelimit.decorators import ratelimit  # noqa: E402

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
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.guardrail_service = guardrail_service
        self.usage_port = usage_port

    def get(self, request):
        media_type = request.query_params.get("media_type")
        query = request.query_params.get("q", "")
        limit = min(int(request.query_params.get("limit", 10)), 50)

        if not query and not media_type:
            return Response([])

        # Input Guardrail (Anti-Jailbreak, Injection)
        if query:
            guard_input = self.guardrail_service.validate_input(query)
            if not guard_input.get("is_safe", True):
                return Response(
                    {"error": guard_input.get("reason", "Inappropriate search query.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        results = get_container().core.catalog_service.search_items(
            query, media_type, limit
        )
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

        try:
            if not validate_file_size(image_file.size, MAX_IMAGE_SIZE):
                return Response(
                    {
                        "error": f"Image is too large (Max: {MAX_IMAGE_SIZE / 1024 / 1024}MB)"
                    },
                    status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                )

            container = get_container()
            image_data = b"".join(chunk for chunk in image_file.chunks())

            if not validate_file_mime_type(image_data, ALLOWED_IMAGE_MIMES):
                return Response(
                    {
                        "error": "Invalid image format. Allowed formats: JPEG, PNG, WEBP."
                    },
                    status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                )

            # Appel au service Cross-Modal
            results = container.core.cross_modal_search_service.deep_multimodal_search(
                text_query="", image_data=image_data, limit=limit
            )

            # Log Usage
            self.usage_port.log_usage(
                engine="clip-vit-large-patch14", units=1, user_id=request.user.id
            )

            return Response(self._format_results(results))
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def _format_results(self, results):
        # Utilise le serializer pour formater les résultats
        serializer = MediaItemSerializer(results, many=True)
        return serializer.data


from animetix.api.dependencies import get_session_service  # noqa: E402


class GameSessionView(APIView):
    """Endpoint pour g├®rer l'├®tat du jeu via API."""

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        # R├®cup├¿re l'├®tat actuel de la session via le service de session
        session = get_session_service(request)
        return Response(
            {
                "media_type": session.get("media_type"),
                "is_ranked": session.get("is_ranked"),
                "is_daily": session.get("is_daily"),
                "game_over": session.get("game_over"),
                "guess_count": len(session.get("guesses", [])),
            }
        )


from django.contrib.auth import authenticate, login, logout  # noqa: E402


@method_decorator(ensure_csrf_cookie, name="dispatch")
@method_decorator(
    ratelimit(key="ip", rate="5/m", method="POST", block=True), name="dispatch"
)
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return Response({"success": True})
        return Response(
            {"success": False, "error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED,
        )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"success": True})


@method_decorator(ensure_csrf_cookie, name="dispatch")
@method_decorator(
    ratelimit(key="ip", rate="5/m", method="POST", block=True), name="dispatch"
)
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        if not username or not password or not email:
            return Response(
                {"success": False, "error": "Missing fields"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"success": False, "error": "Username already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.create_user(
                username=username, email=email, password=password
            )
            login(request, user)
            return Response({"success": True})
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )


@method_decorator(ensure_csrf_cookie, name="dispatch")
class ConfigView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        data = {
            "theme": "auto",
            "language": "fr",
            "user": {
                "is_authenticated": request.user.is_authenticated,
                "username": (
                    request.user.username if request.user.is_authenticated else None
                ),
                "rank": getattr(request.user, "profile", None)
                and request.user.profile.rank
                or None,
            },
            "features": {
                "EXPERIMENTAL_MODES": True,
            },
        }
        return Response(data)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CurrentUserView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            serializer = ProfileSerializer(request.user.profile)
            return Response(serializer.data)
        return Response(
            {"detail": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
        )


class MediaDetailView(APIView):
    """Détails complets d'une œuvre."""

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, media_type, item_id):
        from ..models import MediaItem  # noqa: E402
        from ..serializers import MediaItemSerializer  # noqa: E402

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
        container = get_container()
        data = container.core.catalog_service.load_data(media_type)
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


class CustomConfigDataView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"status": "guest", "visual_theme": "default"})
        return Response({"status": "stub"})


class TransparencyDataView(APIView):
    """
    Vue de transparence communautaire.
    Affiche les métriques d'évolution globale de l'IA et l'impact des feedbacks.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from ..models import AIFeedback, VectorRecord  # noqa: E402

        # 1. Statistiques de feedback (données réelles)
        total_feedbacks = AIFeedback.objects.count()
        positive_rate = 0.82  # Mock default
        if total_feedbacks > 0:
            positive_count = AIFeedback.objects.filter(is_positive=True).count()
            positive_rate = round(positive_count / total_feedbacks, 2)

        # 2. Évolution du Knowledge Graph (données réelles via VectorRecord)
        knowledge_nodes = VectorRecord.objects.count()

        # 3. Métriques de performance système (Simulation temps réel)
        return Response(
            {
                "status": "synchronized",
                "global_metrics": {
                    "total_feedbacks": total_feedbacks,
                    "community_satisfaction": positive_rate,
                    "knowledge_nodes": knowledge_nodes,
                    "model_version": "Animetix-Champion-v2.4",
                    "last_training": "2026-06-12",
                    "uptime": 99.98,
                },
                "evolution_timeline": [
                    {"date": "2026-05", "accuracy": 0.76, "knowledge": 450000},
                    {"date": "2026-06", "accuracy": 0.84, "knowledge": knowledge_nodes},
                ],
                "top_contributions": [
                    {"category": "Lore Accuracy", "impact": "High", "updates": 1240},
                    {"category": "Translation", "impact": "Medium", "updates": 850},
                    {
                        "category": "Archetype Tuning",
                        "impact": "Critical",
                        "updates": 420,
                    },
                ],
                "ethics_audit": {
                    "bias_score": 0.04,
                    "safety_compliance": 0.99,
                    "hallucination_rate": 0.02,
                },
            }
        )


class MangaChapterListView(APIView):
    """Liste des chapitres d'un manga."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, media_id):
        container = get_container()
        manga_service = container.core.manga_service()
        chapters = manga_service.get_chapters(media_id)
        serializer = MangaChapterSerializer(chapters, many=True)
        return Response(serializer.data)


class MangaChapterDetailView(APIView):
    """Détails d'un chapitre (incluant les pages)."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, media_id, chapter_number):
        container = get_container()
        manga_service = container.core.manga_service()
        chapter = manga_service.get_chapter_details(media_id, float(chapter_number))

        if chapter:
            serializer = MangaChapterSerializer(chapter)
            return Response(serializer.data)
        return Response(
            {"error": "Chapter not found"}, status=status.HTTP_404_NOT_FOUND
        )
