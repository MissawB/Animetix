from django.contrib.auth.models import User  # noqa: E402
from pydantic import BaseModel, ConfigDict, Field, ValidationError  # noqa: E402
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import (
    Achievement,
    ClubEvent,
    ClubMembership,
    CreativeFusion,
    DiscoveryClub,
    Notification,
    Profile,
)
from ..serializers import (
    AchievementSerializer,
    ClubEventSerializer,
    CreativeFusionSerializer,
    DiscoveryClubSerializer,
    FriendshipSerializer,
    NotificationSerializer,
    ProfileSerializer,
    SocialUserSerializer,
)


class PersonalizationSchema(BaseModel):
    """Schéma strict pour empêcher les XSS et les injections de JSON volumineux."""

    theme: str = Field(default="auto", pattern="^(auto|dark|light)$")
    accent_color: str = Field(default="blue", pattern="^[a-zA-Z0-9_-]{3,20}$")
    animations_enabled: bool = Field(default=True)
    sound_enabled: bool = Field(default=False)

    model_config = ConfigDict(extra="forbid")


class IsCreatorOrReadOnly(permissions.BasePermission):
    """Permission personnalisée pour autoriser uniquement les créateurs à modifier ou supprimer un objet."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.creator == request.user


class ClubViewSet(viewsets.ModelViewSet):
    """API endpoint pour gérer les clubs de découverte."""

    serializer_class = DiscoveryClubSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsCreatorOrReadOnly]

    def get_queryset(self):
        """
        Sécurisation IDOR & Privacy :
        - Les anonymes voient uniquement les clubs publics.
        - Les authentifiés voient les clubs publics + ceux dont ils sont membres ou créateurs.
        """
        from django.db.models import Count, Prefetch, Q  # noqa: E402

        from ..models import ClubEvent

        user = self.request.user

        # Prefetch events with participants to avoid N+1 in ClubEventSerializer
        events_qs = ClubEvent.objects.all().prefetch_related("participants")

        base_qs = (
            DiscoveryClub.objects.all()
            .select_related("creator")
            .annotate(members_count_annotated=Count("members", distinct=True))
            .prefetch_related("members", Prefetch("events", queryset=events_qs))
        )

        if user.is_authenticated:
            return base_qs.filter(
                Q(is_private=False) | Q(members=user) | Q(creator=user)
            ).distinct()
        return base_qs.filter(is_private=False)

    def get_permissions(self):
        if self.action in ["join", "leave", "trigger_event"]:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def perform_create(self, serializer):
        # Restriction Premium pour la création
        if self.request.user.profile.tier != "premium":
            from rest_framework.exceptions import ValidationError  # noqa: E402

            raise ValidationError("Seuls les membres Premium peuvent fonder des clubs.")

        club = serializer.save(creator=self.request.user)
        # Créateur devient automatiquement Officier
        ClubMembership.objects.create(user=self.request.user, club=club, role="Officer")

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def join(self, request, pk=None):
        club = self.get_object()

        # Limite de 3 clubs pour les comptes gratuits
        if (
            request.user.profile.tier == "free"
            and request.user.club_memberships.count() >= 3
        ):
            return Response(
                {"error": "Limite de 3 clubs atteinte pour les comptes gratuits."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership, created = ClubMembership.objects.get_or_create(
            user=request.user, club=club
        )
        if not created:
            return Response(
                {"status": "already member"}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response({"status": "joined"})

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def leave(self, request, pk=None):
        club = self.get_object()
        ClubMembership.objects.filter(user=request.user, club=club).delete()
        return Response({"status": "left"})

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def trigger_event(self, request, pk=None):
        club = self.get_object()
        # Vérification si l'utilisateur est Officier
        try:
            membership = ClubMembership.objects.get(user=request.user, club=club)
            if membership.role != "Officer":
                return Response(
                    {"error": "Seuls les officiers peuvent lancer des événements."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except ClubMembership.DoesNotExist:
            return Response(
                {"error": "Vous n'êtes pas membre de ce club."},
                status=status.HTTP_403_FORBIDDEN,
            )

        event_id = request.data.get("event_id")
        from animetix.tasks_client import enqueue_task  # noqa: E402

        enqueue_task("trigger_club_event", club.id, event_id)
        return Response({"status": "event triggered"})


class ProfileViewSet(viewsets.ModelViewSet):
    """API endpoint pour visualiser et modifier les profils utilisateurs."""

    queryset = Profile.objects.all().select_related("user")
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "user__username"

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        serializer = self.get_serializer(request.user.profile)
        return Response(serializer.data)

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def update_personalization(self, request):
        try:
            # Validation stricte du JSON entrant via Pydantic
            validated_data = PersonalizationSchema(**request.data).model_dump()

            profile = request.user.profile
            profile.personalization_settings = validated_data
            profile.save()
            return Response(
                {"status": "updated", "settings": profile.personalization_settings}
            )
        except ValidationError as e:
            # En cas de payload non conforme (clés interdites, valeurs erronées), on bloque
            return Response(
                {"error": "Invalid personalization settings.", "details": e.errors()},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=False,
        methods=["patch"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def update_settings(self, request):
        profile = request.user.profile

        # Autoriser uniquement la mise à jour du tier (en environnement de démo) et des infos liées
        tier = request.data.get("tier")
        if tier in dict(Profile.TIERS).keys():
            profile.tier = tier

        custom_color = request.data.get("custom_username_color")
        if custom_color is not None:
            badges = (
                list(profile.unlocked_badges)
                if isinstance(profile.unlocked_badges, list)
                else []
            )
            if "Sponsor Or" in badges:
                import re  # noqa: E402

                if custom_color == "" or re.match(
                    r"^#(?:[0-9a-fA-F]{3}){1,2}$", custom_color
                ):
                    profile.custom_username_color = custom_color or None
                else:
                    return Response(
                        {"error": "Invalid color format. Use hex color e.g. #FFD700"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                return Response(
                    {
                        "error": "Vous devez soutenir le serveur pour personnaliser votre couleur de pseudo."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        profile.save()
        return Response(
            {
                "status": "updated",
                "tier": profile.tier,
                "custom_username_color": profile.custom_username_color,
                "unlocked_badges": profile.unlocked_badges,
            }
        )

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def claim_donation(self, request):
        profile = request.user.profile
        badges = (
            list(profile.unlocked_badges)
            if isinstance(profile.unlocked_badges, list)
            else []
        )
        if "Sponsor Or" not in badges:
            badges.append("Sponsor Or")
            profile.unlocked_badges = badges

        if not profile.custom_username_color:
            profile.custom_username_color = "#FFD700"

        profile.save()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def refill_quota(self, request):
        """
        Réinitialise l'utilisation quotidienne de quota de l'utilisateur
        et crédite un bonus de secours de 1000 Bx.
        """
        from django.utils import timezone  # noqa: E402

        from ..models import AITokenUsage, WalletTransaction  # noqa: E402

        today = timezone.now().date()
        deleted_count, _ = AITokenUsage.objects.filter(
            user=request.user, created_at__date=today
        ).delete()

        # Bonus de secours
        amount = 1000
        profile = request.user.profile
        profile.wallet_balance += amount
        profile.save()

        WalletTransaction.objects.create(
            user=request.user,
            amount=amount,
            transaction_type="daily_grant",
            description="Recharge de secours (Reset Quota)",
        )

        return Response(
            {
                "status": "refilled",
                "deleted_records": deleted_count,
                "new_balance": profile.wallet_balance,
                "message": "Votre quota a été réinitialisé et 1000 Bx ont été injectés.",
            }
        )

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def generate_api_key(self, request):
        import uuid  # noqa: E402

        profile = request.user.profile
        new_key = f"atx_{uuid.uuid4().hex}"
        profile.set_api_key(new_key)
        profile.save()
        return Response(
            {
                "api_key": new_key,
                "message": "Store this key safely. It will not be shown again.",
            }
        )

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def revoke_api_key(self, request):
        profile = request.user.profile
        profile.api_key_hash = None
        profile.save()
        return Response({"status": "revoked"})


class UserSearchView(APIView):
    """Recherche d'utilisateurs par pseudo."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "")
        if len(query) < 2:
            return Response([])

        users = (
            User.objects.filter(username__icontains=query)
            .exclude(id=request.user.id)
            .select_related("profile")[:20]
        )
        serializer = SocialUserSerializer(users, many=True)

        # Ajouter l'info si on le suit déjà
        data = serializer.data
        following_ids = request.user.following.values_list("to_user_id", flat=True)
        for item in data:
            item["is_following"] = item["id"] in following_ids

        return Response(data)


class CreativeFusionViewSet(viewsets.ModelViewSet):
    """API endpoint pour visualiser, créer, liker et remixer des fusions créatives."""

    serializer_class = CreativeFusionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsCreatorOrReadOnly]

    def perform_create(self, serializer):
        """Assigne automatiquement le créateur à l'utilisateur connecté."""
        serializer.save(creator=self.request.user)

    def get_queryset(self):
        """
        Prévention IDOR : Un utilisateur ne peut voir que les fusions publiques
        ou ses propres fusions privées.
        """
        from django.db.models import Q  # noqa: E402

        user = self.request.user

        # Base : select_related and prefetch_related to avoid N+1 queries
        base_qs = (
            CreativeFusion.objects.all()
            .select_related("creator", "creator__profile", "parent")
            .prefetch_related("likes")
            .order_by("-created_at")
        )

        if user.is_authenticated:
            # L'utilisateur voit les fusions publiques ET ses propres fusions
            return base_qs.filter(Q(is_public=True) | Q(creator=user))
        else:
            # Un anonyme ne voit que les fusions publiques
            return base_qs.filter(is_public=True)

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def like(self, request, pk=None):
        fusion = (
            self.get_object()
        )  # get_object utilise get_queryset, la sécurité IDOR est donc automatique
        if request.user in fusion.likes.all():
            fusion.likes.remove(request.user)
            return Response({"status": "unliked", "likes_count": fusion.likes.count()})
        else:
            fusion.likes.add(request.user)
            return Response({"status": "liked", "likes_count": fusion.likes.count()})

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def remix(self, request, pk=None):
        parent = self.get_object()  # Sécurité IDOR automatique via get_queryset()
        remix = CreativeFusion.objects.create(
            title_a=parent.title_a,
            title_b=parent.title_b,
            media_type_a=parent.media_type_a,
            media_type_b=parent.media_type_b,
            chaos_level=request.data.get("chaos_level", parent.chaos_level),
            universe_balance=request.data.get(
                "universe_balance", parent.universe_balance
            ),
            art_style=request.data.get("art_style", parent.art_style),
            creator=request.user,
            parent=parent,
            scenario_text="Remix en cours...",
            is_public=request.data.get("is_public", True),
        )
        serializer = self.get_serializer(remix)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SocialViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        # La page Communauté est publique. Le décorateur @action ne suffit pas
        # ici car les vues sont câblées manuellement (.as_view({"get": ...})),
        # ce qui ignore ses permission_classes — on tranche donc par action.
        if self.action == "dashboard":
            return [permissions.AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        # Page Communauté publique : un anonyme charge le hub avec un réseau
        # vide. Le réseau personnel n'apparaît qu'une fois connecté.
        if not request.user.is_authenticated:
            return Response({"following": [], "followers": []})
        following = request.user.following.all().select_related(
            "to_user", "to_user__profile", "from_user", "from_user__profile"
        )
        followers = request.user.followers.all().select_related(
            "to_user", "to_user__profile", "from_user", "from_user__profile"
        )
        return Response(
            {
                "following": FriendshipSerializer(following, many=True).data,
                "followers": FriendshipSerializer(followers, many=True).data,
            }
        )

    @action(detail=True, methods=["post"])
    def toggle_follow(self, request, pk=None):
        try:
            target_user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if target_user == request.user:
            return Response(
                {"error": "Cannot follow yourself"}, status=status.HTTP_400_BAD_REQUEST
            )

        from ..models import Friendship  # noqa: E402

        friendship, created = Friendship.objects.get_or_create(
            from_user=request.user, to_user=target_user
        )
        if not created:
            friendship.delete()
            return Response({"status": "unfollowed"})
        else:
            return Response({"status": "followed"})


class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    # Public, read-only catalogue of achievements.
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer


class LeaderboardView(APIView):
    """Calcul dynamique du classement mondial basé sur les points classés."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        mode = request.query_params.get("mode", "ranked")  # 'ranked' or 'xp'

        if mode == "xp":
            top_profiles = Profile.objects.select_related("user").order_by("-xp")[:10]
        else:
            top_profiles = Profile.objects.select_related("user").order_by(
                "-ranked_points"
            )[:10]

        data = []
        for i, p in enumerate(top_profiles):
            data.append(
                {
                    "position": i + 1,
                    "username": p.user.username,
                    "points": p.ranked_points if mode == "ranked" else p.xp,
                    "level": p.level,
                    "is_me": request.user == p.user,
                }
            )
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
        data["achievements_count"] = user.userachievement_set.count()
        data["collection_count"] = CreativeFusion.objects.filter(creator=user).count()
        data["recent_achievements"] = AchievementSerializer(
            Achievement.objects.filter(userachievement__user=user).order_by(
                "-userachievement__unlocked_at"
            )[:5],
            many=True,
        ).data
        fusions_qs = (
            CreativeFusion.objects.filter(creator=user)
            .select_related("creator")
            .prefetch_related("likes")
        )
        data["top_fusions"] = CreativeFusionSerializer(
            fusions_qs.order_by("-likes")[:4],
            many=True,
        ).data
        data["recent_fusions"] = CreativeFusionSerializer(
            fusions_qs.order_by("-created_at")[:5],
            many=True,
        ).data
        return Response(data)


class MyCollectionView(APIView):
    """Récupère la collection de fusions de l'utilisateur connecté."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        fusions = (
            CreativeFusion.objects.filter(creator=request.user)
            .select_related("creator", "creator__profile", "parent")
            .prefetch_related("likes")
            .order_by("-created_at")
        )
        liked_fusions = (
            request.user.liked_fusions.all()
            .select_related("creator", "creator__profile", "parent")
            .prefetch_related("likes")
            .order_by("-created_at")
        )

        return Response(
            {
                "my_creations": CreativeFusionSerializer(fusions, many=True).data,
                "my_likes": CreativeFusionSerializer(liked_fusions, many=True).data,
            }
        )


class NotificationListView(APIView):
    """Liste des notifications de l'utilisateur."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifs = Notification.objects.filter(user=request.user).order_by("-created_at")[
            :50
        ]
        # Marquer comme lues
        notifs.update(is_read=True)
        return Response(NotificationSerializer(notifs, many=True).data)

    def post(self, request):
        notifs = Notification.objects.filter(user=request.user).order_by("-created_at")[
            :50
        ]
        notifs.update(is_read=True)
        return Response({"status": "success"})


class GameplaySessionListView(APIView):
    """Liste l'historique des sessions de jeu de l'utilisateur connecté."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        limit = int(request.GET.get("limit", 50))
        from ..models import GameplaySession  # noqa: E402
        from ..serializers import GameplaySessionSerializer  # noqa: E402

        sessions = GameplaySession.objects.filter(user=request.user).order_by(
            "-created_at"
        )[:limit]
        return Response(GameplaySessionSerializer(sessions, many=True).data)


class ClubEventViewSet(viewsets.ModelViewSet):
    """API endpoint pour gérer les événements de clubs."""

    serializer_class = ClubEventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = (
            ClubEvent.objects.all()
            .prefetch_related("participants")
            .order_by("event_date")
        )
        club_id = self.request.query_params.get("club")
        if club_id:
            queryset = queryset.filter(club_id=club_id)
        return queryset

    def perform_create(self, serializer):
        club = serializer.validated_data["club"]
        try:
            membership = ClubMembership.objects.get(user=self.request.user, club=club)
            if membership.role != "Officer":
                from rest_framework.exceptions import PermissionDenied  # noqa: E402

                raise PermissionDenied(
                    "Seuls les officiers peuvent créer des événements."
                )
        except ClubMembership.DoesNotExist:
            from rest_framework.exceptions import PermissionDenied  # noqa: E402

            raise PermissionDenied("Vous n'êtes pas membre de ce club.")
        serializer.save()

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def join(self, request, pk=None):
        event = self.get_object()
        # Vérifier si l'utilisateur est membre du club
        try:
            ClubMembership.objects.get(user=request.user, club=event.club)
        except ClubMembership.DoesNotExist:
            return Response(
                {
                    "error": "Vous devez être membre du club pour participer à cet événement."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if request.user in event.participants.all():
            event.participants.remove(request.user)
            return Response(
                {"status": "left", "participants_count": event.participants.count()}
            )
        else:
            event.participants.add(request.user)
            return Response(
                {"status": "joined", "participants_count": event.participants.count()}
            )
