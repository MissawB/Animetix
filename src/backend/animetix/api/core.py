from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from ..models import Profile, DailyChallenge, Achievement, CreativeFusion, GameplaySession
from ..serializers import (ProfileSerializer, DailyChallengeSerializer, AchievementSerializer, 
                            MediaItemSerializer, CreativeFusionSerializer, FriendshipSerializer)
from ..containers import get_container
from ..session_manager import GameSessionManager
from django.contrib.auth.models import User
import random
import datetime
import base64
import hashlib
import requests
from django.core.cache import cache
from django.http import HttpResponse

def image_proxy_view(request):

    """Proxy pour les images externes avec cache local."""
    encoded_url = request.GET.get('url')
    if not encoded_url: return HttpResponse(status=400)
    
    try:
        url = base64.b64decode(encoded_url).decode('utf-8')
    except:
        return HttpResponse(status=400)

    cache_key = f"img_cache_{hashlib.md5(url.encode()).hexdigest()}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return HttpResponse(cached_data['content'], content_type=cached_data['content_type'])

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            content = response.content
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            cache.set(cache_key, {'content': content, 'content_type': content_type}, 60*60*24*7)
            return HttpResponse(content, content_type=content_type)
    except Exception as e:
        print(f"ÔØî Image Proxy Error: {e}")
        
    return HttpResponse(status=404)

from ..serializers import CreativeFusionSerializer, FriendshipSerializer, SocialUserSerializer

class MediaSearchView(APIView):
    """Recherche d'œuvres via SQL ou Multi-Modale (CLIP)."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        media_type = request.query_params.get('media_type')
        query = request.query_params.get('q', '')
        limit = min(int(request.query_params.get('limit', 10)), 50)

        if not query and not media_type:
            return Response([])

        results = get_container().catalog_service.search_items(query, media_type, limit)
        return Response(self._format_results(results))

    def post(self, request):
        """Recherche par image (Cross-Modal)."""
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

            return Response(self._format_results(results))
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    def _format_results(self, results):
        formatted = []
        for item in results:
            formatted.append({
                'id': item.get('id'),
                'title': item.get('title'),
                'title_english': item.get('title_english'),
                'image': item.get('image'),
                'type': item.get('type'),
                'score': item.get('score', 1.0)
            })
        return formatted

            
        return Response(formatted_results)

class GameSessionView(APIView):
    """Endpoint pour g├®rer l'├®tat du jeu via API."""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        # R├®cup├¿re l'├®tat actuel de la session (compatible avec l'existant)
        return Response({
            "media_type": request.session.get('media_type'),
            "is_ranked": request.session.get('is_ranked'),
            "is_daily": request.session.get('is_daily'),
            "game_over": request.session.get('game_over'),
            "guess_count": len(request.session.get('guesses', []))
        })


from ..session_manager import GameSessionManager

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
            return Response({
                "id": request.user.id,
                "username": request.user.username,
                "email": request.user.email
            })
        return Response({"detail": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)


