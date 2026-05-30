from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from dependency_injector.wiring import inject, Provide
from ..models import Profile, DailyChallenge, Achievement, CreativeFusion, GameplaySession
from ..serializers import (ProfileSerializer, DailyChallengeSerializer, AchievementSerializer, 
                            MediaItemSerializer, CreativeFusionSerializer, FriendshipSerializer)
from ..containers import get_container, Container
from core.domain.services.guardrail_service import GuardrailService
from core.ports.usage_port import UsagePort
from django.contrib.auth.models import User
import random
import datetime
import base64
import hashlib
import httpx
import socket
import ipaddress
from urllib.parse import urlparse
from animetix_project.logging_config import get_logger
from core.utils.security import is_safe_url
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

logger = get_logger('animetix.api')

def image_proxy_view(request):

    """Proxy pour les images externes avec cache local."""
    encoded_url = request.GET.get('url')
    if not encoded_url: return HttpResponse(status=400)
    
    try:
        url = base64.b64decode(encoded_url).decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to decode image proxy URL: {e}")
        return HttpResponse(status=400)

    # Protection SSRF
    if not is_safe_url(url):
        logger.warning(f"Blocked unsafe URL in image proxy: {url}")
        return HttpResponse("Forbidden: Unsafe URL", status=403)

    cache_key = f"img_cache_{hashlib.md5(url.encode()).hexdigest()}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return HttpResponse(cached_data['content'], content_type=cached_data['content_type'])

    try:
        response = httpx.get(url, timeout=10, follow_redirects=False)
        if response.status_code == 200:
            content = response.content
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            cache.set(cache_key, {'content': content, 'content_type': content_type}, 60*60*24*7)
            return HttpResponse(content, content_type=content_type)
        elif response.status_code in (301, 302, 303, 307, 308):
            logger.warning(f"Blocked redirect attempt in image proxy: {url} -> {response.headers.get('Location')}")
            return HttpResponse("Forbidden: Redirects not allowed", status=403)
    except Exception as e:
        logger.error("Image Proxy Error: %s", e, exc_info=True)
        
    return HttpResponse(status=404)

from ..serializers import CreativeFusionSerializer, FriendshipSerializer, SocialUserSerializer

class MediaSearchView(APIView):
    """Recherche d'œuvres via SQL ou Multi-Modale (CLIP)."""
    permission_classes = [permissions.AllowAny]

    @inject
    def __init__(self, 
                 guardrail_service: GuardrailService = Provide[Container.core.guardrail_service],
                 usage_port: UsagePort = Provide[Container.infrastructure.usage_port],
                 **kwargs):
        super().__init__(**kwargs)
        self.guardrail_service = guardrail_service
        self.usage_port = usage_port

    def get(self, request):
        media_type = request.query_params.get('media_type')
        query = request.query_params.get('q', '')
        limit = min(int(request.query_params.get('limit', 10)), 50)

        if not query and not media_type:
            return Response([])

        # Input Guardrail (Anti-Jailbreak, Injection)
        if query:
            guard_input = self.guardrail_service.validate_input(query)
            if not guard_input.get("is_safe", True):
                return Response(
                    {"error": guard_input.get("reason", "Inappropriate search query.")},
                    status=status.HTTP_400_BAD_REQUEST
                )

        results = get_container().catalog_service.search_items(query, media_type, limit)
        return Response(self._format_results(results))

    def post(self, request):
        """Recherche par image (Cross-Modal). Requiert Authentification + Quota."""
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required for image search."}, status=status.HTTP_401_UNAUTHORIZED)

        # Quota Check
        tier = getattr(request, 'user_tier', 'free')
        if not self.usage_port.check_quota(request.user.id, tier):
             return Response({"error": "Daily AI quota exceeded."}, status=status.HTTP_403_FORBIDDEN)

        image_file = request.FILES.get('image')
        media_type = request.data.get('media_type', 'Anime')
        limit = min(int(request.data.get('limit', 10)), 20)

        if not image_file:
            return Response({'error': 'No image provided'}, status=400)

        try:
            container = get_container()
            image_data = image_file.read()

            # Appel au service Cross-Modal
            results = container.cross_modal_search.deep_multimodal_search(
                text_query="", 
                image_data=image_data, 
                limit=limit
            )

            # Log Usage
            self.usage_port.log_usage(engine="clip-vit-large-patch14", units=1, user_id=request.user.id)

            return Response(self._format_results(results))
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    def _format_results(self, results):
        # Utilise le serializer pour formater les résultats
        serializer = MediaItemSerializer(results, many=True)
        return serializer.data

            
        return Response(formatted_results)

from animetix.api.dependencies import get_session_service

class GameSessionView(APIView):
    """Endpoint pour g├®rer l'├®tat du jeu via API."""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        # R├®cup├¿re l'├®tat actuel de la session via le service de session
        session = get_session_service(request)
        return Response({
            "media_type": session.get('media_type'),
            "is_ranked": session.get('is_ranked'),
            "is_daily": session.get('is_daily'),
            "game_over": session.get('game_over'),
            "guess_count": len(session.get('guesses', []))
        })


from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='dispatch')
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return Response({"success": True})
        return Response({"success": False, "error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"success": True})


@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='dispatch')
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if not username or not password or not email:
            return Response({"success": False, "error": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"success": False, "error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            return Response({"success": True})
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ConfigView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        data = {
            'theme': 'auto',
            'language': 'fr',
            'user': {
                'is_authenticated': request.user.is_authenticated,
                'username': request.user.username if request.user.is_authenticated else None,
                'rank': getattr(request.user, 'profile', None) and request.user.profile.rank or None,
            },
            'features': {
                'EXPERIMENTAL_MODES': True,
            }
        }
        return Response(data)


class CurrentUserView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            serializer = ProfileSerializer(request.user.profile)
            return Response(serializer.data)
        return Response({"detail": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

class MediaDetailView(APIView):
    """Détails complets d'une œuvre."""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, media_type, item_id):
        container = get_container()
        data = container.catalog_service.load_data(media_type)
        if not data:
            return Response({'error': 'Media type not found'}, status=404)
        
        # Recherche par ID dans la DB
        item = next((i for i in data.get('db', []) if str(i.get('id')) == str(item_id)), None)
        if not item:
            return Response({'error': 'Item not found'}, status=404)
            
        # Enrichissement avec les nœuds du graphe si présents
        graph_nodes = item.get('graph_nodes', {})
        item['studios'] = graph_nodes.get('studios', [])
        item['author'] = graph_nodes.get('author')
        item['related_items'] = graph_nodes.get('related_items', [])

        serializer = MediaItemSerializer(item)
        return Response(serializer.data)


