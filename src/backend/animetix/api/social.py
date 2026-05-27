from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from ..models import Profile, CreativeFusion, Achievement, DailyChallenge, Notification
from ..serializers import (ProfileSerializer, CreativeFusionSerializer, AchievementSerializer, 
                            FriendshipSerializer, DailyChallengeSerializer, NotificationSerializer,
                            DiscoveryClubSerializer, ClubMembershipSerializer)
from django.contrib.auth.models import User
from django.db.models import F
from ..models import DiscoveryClub, ClubMembership

class ClubViewSet(viewsets.ModelViewSet):
    """API endpoint pour gérer les clubs de découverte."""
    queryset = DiscoveryClub.objects.all()
    serializer_class = DiscoveryClubSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        # Restriction Premium : Seuls les utilisateurs Premium/Pro peuvent créer des clubs
        if self.request.user.profile.tier == 'free':
            raise permissions.exceptions.PermissionDenied("Seuls les membres Premium peuvent créer des clubs.")
        
        club = serializer.save(creator=self.request.user)
        # Le créateur devient automatiquement admin/owner
        ClubMembership.objects.create(user=self.request.user, club=club, role='owner')

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def join(self, request, pk=None):
        club = self.get_object()
        user = request.user
        
        # Limite de 3 clubs pour les utilisateurs gratuits
        if user.profile.tier == 'free' and user.joined_clubs.count() >= 3:
            return Response({"error": "Limite de 3 clubs atteinte pour les comptes gratuits."}, status=status.HTTP_400_BAD_REQUEST)
            
        membership, created = ClubMembership.objects.get_or_create(user=user, club=club)
        if not created:
            return Response({"message": "Déjà membre."}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({"status": "joined"}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def leave(self, request, pk=None):
        club = self.get_object()
        try:
            membership = ClubMembership.objects.get(user=request.user, club=club)
            if membership.role == 'owner':
                return Response({"error": "Le propriétaire ne peut pas quitter le club sans le supprimer ou transférer la propriété."}, status=status.HTTP_400_BAD_REQUEST)
            membership.delete()
            return Response({"status": "left"})
        except ClubMembership.DoesNotExist:
            return Response({"error": "Non membre."}, status=status.HTTP_400_BAD_REQUEST)

class ProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint pour visualiser les profils utilisateurs."""
    queryset = Profile.objects.all().select_related('user')
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user.profile)
        return Response(serializer.data)

class CreativeFusionViewSet(viewsets.ModelViewSet):
    """API endpoint pour visualiser, créer, liker et remixer des fusions créatives."""
    queryset = CreativeFusion.objects.all().order_by('-created_at')
    serializer_class = CreativeFusionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        fusion = self.get_object()
        if request.user in fusion.likes.all():
            fusion.likes.remove(request.user)
            return Response({'status': 'unliked', 'likes_count': fusion.likes.count()})
        else:
            fusion.likes.add(request.user)
            return Response({'status': 'liked', 'likes_count': fusion.likes.count()})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def remix(self, request, pk=None):
        parent = self.get_object()
        remix = CreativeFusion.objects.create(
            title_a=parent.title_a,
            title_b=parent.title_b,
            media_type_a=parent.media_type_a,
            media_type_b=parent.media_type_b,
            chaos_level=request.data.get('chaos_level', parent.chaos_level),
            universe_balance=request.data.get('universe_balance', parent.universe_balance),
            art_style=request.data.get('art_style', parent.art_style),
            creator=request.user,
            parent=parent,
            scenario_text="Remix en cours..."
        )
        serializer = self.get_serializer(remix)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SocialViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        following = request.user.following.all().select_related('to_user__profile')
        followers = request.user.followers.all().select_related('from_user__profile')
        return Response({
            'following': FriendshipSerializer(following, many=True).data,
            'followers': FriendshipSerializer(followers, many=True).data,
        })

    @action(detail=True, methods=['post'])
    def toggle_follow(self, request, pk=None):
        try:
            target_user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            
        if target_user == request.user: 
            return Response({"error": "Cannot follow yourself"}, status=status.HTTP_400_BAD_REQUEST)
            
        from ..models import Friendship
        friendship, created = Friendship.objects.get_or_create(from_user=request.user, to_user=target_user)
        if not created: 
            friendship.delete()
            return Response({'status': 'unfollowed'})
        else: 
            return Response({'status': 'followed'})

class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer

class LeaderboardView(APIView):
    """Calcul dynamique du classement mondial basé sur les points classés."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        mode = request.query_params.get('mode', 'ranked') # 'ranked' or 'xp'
        
        if mode == 'xp':
            top_profiles = Profile.objects.order_by('-xp')[:10]
        else:
            top_profiles = Profile.objects.order_by('-ranked_points')[:10]
            
        data = []
        for i, p in enumerate(top_profiles):
            data.append({
                'position': i + 1,
                'username': p.user.username,
                'points': p.ranked_points if mode == 'ranked' else p.xp,
                'level': p.level,
                'is_me': request.user == p.user
            })
        return Response(data)

class ProfileDetailView(APIView):
    """Récupère les détails publics d'un utilisateur."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
            profile = user.profile
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
            
        serializer = ProfileSerializer(profile)
        # On ajoute les succès et les fusions récentes
        data = serializer.data
        data['recent_fusions'] = CreativeFusionSerializer(
            CreativeFusion.objects.filter(creator=user).order_by('-created_at')[:5], 
            many=True
        ).data
        return Response(data)

class MyCollectionView(APIView):
    """Récupère la collection de fusions de l'utilisateur connecté."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        fusions = CreativeFusion.objects.filter(creator=request.user).order_by('-created_at')
        liked_fusions = request.user.liked_fusions.all().order_by('-created_at')
        
        return Response({
            'my_creations': CreativeFusionSerializer(fusions, many=True).data,
            'my_likes': CreativeFusionSerializer(liked_fusions, many=True).data
        })

class NotificationListView(APIView):
    """Liste des notifications de l'utilisateur."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifs = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
        # Marquer comme lues
        notifs.update(is_read=True)
        return Response(NotificationSerializer(notifs, many=True).data)
