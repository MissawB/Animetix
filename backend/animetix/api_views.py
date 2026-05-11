from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Profile, DailyChallenge, Achievement
from .serializers import ProfileSerializer, DailyChallengeSerializer, AchievementSerializer, MediaItemSerializer
from .services import AnimetixService
import random

animetix_service = AnimetixService()

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
    """Recherche d'œuvres via ChromaDB (Backend-agnostic)."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        media_type = request.query_params.get('media_type', 'Anime')
        query = request.query_params.get('q', '')
        limit = int(request.query_params.get('limit', 10))
        
        data = animetix_service.load_data(media_type)
        if not data:
            return Response({"error": "Media type not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Si query vide, retourne les plus populaires
        if not query:
            results = data['lookup'][:limit]
            return Response(results)
        
        # Recherche sémantique via Chroma
        coll_name = f"{media_type.lower()}_thematic"
        if media_type == 'Character': coll_name = "character_vibe"
        
        try:
            # Note: Pour une recherche par texte, on devrait d'abord vectoriser le texte
            # Mais ici pour l'API on peut aussi faire une recherche par titre exacte 
            # ou renvoyer le lookup filtré pour l'autocomplétion.
            results = [item for item in data['lookup'] if query.lower() in item['title'].lower()][:limit]
            return Response(results)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
