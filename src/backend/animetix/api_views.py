from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Profile, DailyChallenge, Achievement, CreativeFusion
from .serializers import ProfileSerializer, DailyChallengeSerializer, AchievementSerializer, MediaItemSerializer, CreativeFusionSerializer
from .containers import get_container
import random

class CreativeFusionViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows creative fusions to be viewed."""
    queryset = CreativeFusion.objects.all().order_by('-created_at')
    serializer_class = CreativeFusionSerializer

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
        print(f"❌ Image Proxy Error: {e}")
        
    return HttpResponse(status=404)

class ProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user.profile)
        return Response(serializer.data)

class DailyChallengeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DailyChallenge.objects.all()
    serializer_class = DailyChallengeSerializer
    permission_classes = [permissions.AllowAny]

class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer

class MediaSearchView(APIView):
    """Recherche d'œuvres via SQL (Source of Truth) pour autocomplétion performante."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        media_type = request.query_params.get('media_type')
        query = request.query_params.get('q', '')
        limit = min(int(request.query_params.get('limit', 10)), 50)
        
        if not query and not media_type:
            return Response([])

        # Utilisation de la méthode de recherche SQL centralisée
        results = get_container().catalog_service.search_items(query, media_type, limit)

        
        # Formatage pour le composant d'autocomplétion
        formatted_results = []
        for item in results:
            formatted_results.append({
                'id': item.get('id'),
                'title': item.get('title'),
                'title_english': item.get('title_english'),
                'image': item.get('image'),
                'type': item.get('type')
            })
            
        return Response(formatted_results)

class GameSessionView(APIView):
    """Endpoint pour gérer l'état du jeu via API."""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        # Récupère l'état actuel de la session (compatible avec l'existant)
        return Response({
            "media_type": request.session.get('media_type'),
            "is_ranked": request.session.get('is_ranked'),
            "is_daily": request.session.get('is_daily'),
            "game_over": request.session.get('game_over'),
            "guess_count": len(request.session.get('guesses', []))
        })
