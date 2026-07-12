from django.contrib.auth.models import User
from rest_framework import serializers

from .models import (
    Achievement,
    BossParticipation,
    ClubEvent,
    ClubMembership,
    CreativeFusion,
    DailyChallenge,
    DataCurationTicket,
    DiscoveryClub,
    FavoriteManga,
    GlobalBoss,
    MangaChapter,
    MangaPage,
    Profile,
    TrackerConnection,
    VoiceProfile,
)


class TrackerConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackerConnection
        fields = ["id", "tracker", "username", "created_at"]


class MangaPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MangaPage
        fields = ["id", "number", "image_url", "metadata"]


class MangaChapterSerializer(serializers.ModelSerializer):
    pages = MangaPageSerializer(many=True, read_only=True)

    class Meta:
        model = MangaChapter
        fields = [
            "id",
            "manga",
            "number",
            "title",
            "external_id",
            "pages",
            "created_at",
            "updated_at",
        ]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class UserAdminSerializer(serializers.ModelSerializer):
    level = serializers.IntegerField(source="profile.level", read_only=True)
    tier = serializers.CharField(source="profile.tier", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_staff",
            "is_active",
            "date_joined",
            "level",
            "tier",
        ]
        read_only_fields = ["date_joined"]


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    rank = serializers.ReadOnlyField()
    has_api_key = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            "id",
            "user",
            "xp",
            "current_streak",
            "max_streak",
            "last_win_date",
            "total_wins",
            "total_games",
            "ranked_points",
            "ranked_max_points",
            "rank",
            "unlocked_badges",
            "custom_username_color",
            "tier",
            "wallet_balance",
            "personalization_settings",
            "has_api_key",
        ]

    def get_has_api_key(self, obj):
        return bool(obj.api_key_hash)


class DailyChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyChallenge
        fields = "__all__"


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = "__all__"


# --- VS Battle (Arena) : serializers de réponse pour drf-spectacular ---
# Décrivent la forme renvoyée par `run_vs_battle` afin que les types soient
# générés dans `schema.yaml`/`api.d.ts` (au lieu d'être écrits à la main côté front).
class CombatStatsSerializer(serializers.Serializer):
    tier = serializers.CharField(allow_null=True, required=False)
    tier_value = serializers.IntegerField()
    speed = serializers.CharField(allow_null=True, required=False)
    durability = serializers.CharField(allow_null=True, required=False)
    intelligence = serializers.CharField(allow_null=True, required=False)
    abilities = serializers.ListField(child=serializers.CharField(), required=False)


class CombatCharacterSerializer(serializers.Serializer):
    name = serializers.CharField()
    franchise = serializers.CharField(allow_null=True, required=False)
    image_url = serializers.CharField(allow_null=True, required=False)
    wiki_url = serializers.CharField(allow_null=True, required=False)
    stats = CombatStatsSerializer()
    summary = serializers.CharField(required=False)


class DebateTurnSerializer(serializers.Serializer):
    agent = serializers.CharField()
    content = serializers.CharField()


class VsBattleResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    character_a = CombatCharacterSerializer()
    character_b = CombatCharacterSerializer()
    winner = serializers.CharField()
    verdict_summary = serializers.CharField()
    debate_history = DebateTurnSerializer(many=True)


# --- XAI / Diagnostics : serializers de réponse pour drf-spectacular ---
# Décrivent la charge de l'évènement SSE `xai_report` émis par AgenticRAGStreamView,
# afin de générer les types structurés côté front (au lieu de les écrire à la main).
class DocumentAttributionSerializer(serializers.Serializer):
    title = serializers.CharField()
    contribution_weight = serializers.FloatField()
    relevance_score = serializers.FloatField(required=False)
    document_id = serializers.CharField(required=False)


class LogitLensTrajectorySerializer(serializers.Serializer):
    layer = serializers.IntegerField()
    top_tokens = serializers.ListField(child=serializers.CharField())
    internal_probabilities = serializers.ListField(child=serializers.FloatField())


class ModelDiagnosticsSerializer(serializers.Serializer):
    attention_heatmap = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField())
    )
    top_influential_tokens = serializers.ListField(child=serializers.CharField())
    logit_lens_trajectory = LogitLensTrajectorySerializer(many=True)


class UncertaintySerializer(serializers.Serializer):
    confidence_score = serializers.FloatField()
    is_reliable = serializers.BooleanField()
    perplexity = serializers.FloatField(allow_null=True)
    action_required = serializers.CharField()
    method = serializers.CharField()


class AgentTraceStepSerializer(serializers.Serializer):
    agent = serializers.CharField()
    thought = serializers.CharField()


class XaiReportSerializer(serializers.Serializer):
    query_intent = serializers.CharField()
    # Conteneurs optionnels : le backend peut les omettre (défauts pydantic),
    # les consommateurs front gardent déjà leur absence.
    retrieval_attribution = DocumentAttributionSerializer(many=True, required=False)
    internal_diagnostics = ModelDiagnosticsSerializer(required=False)
    uncertainty = UncertaintySerializer(required=False)
    agent_trace = AgentTraceStepSerializer(many=True, required=False)
    final_confidence = serializers.FloatField()


from core.utils.security import sanitize_html_content  # noqa: E402


# Serializers pour les données chargées dynamiquement (JSON/pgvector)
class MediaItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    title_english = serializers.CharField(required=False, allow_null=True)
    title_native = serializers.CharField(required=False, allow_null=True)
    image = serializers.URLField(required=False, allow_null=True)
    # Aliases the search UI consumes: item.type (tab filtering + detail route)
    # and item.image_url (thumbnails). Without them: no images, empty tabs, and
    # links resolving to /media/undefined/{id}/.
    type = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    year = serializers.IntegerField(required=False, allow_null=True)
    popularity = serializers.IntegerField(required=False, allow_null=True)
    genres = serializers.ListField(child=serializers.CharField(), required=False)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    micro_tags = serializers.ListField(child=serializers.CharField(), required=False)
    description = serializers.CharField(required=False, allow_null=True)

    # Knowledge Graph Nodes
    studios = serializers.ListField(child=serializers.CharField(), required=False)
    author = serializers.CharField(required=False, allow_null=True)
    related_items = serializers.ListField(child=serializers.DictField(), required=False)

    @staticmethod
    def _media_type(obj):
        if isinstance(obj, dict):
            return obj.get("media_type") or obj.get("type")
        return getattr(obj, "media_type", None)

    def get_type(self, obj):
        return self._media_type(obj)

    def get_image_url(self, obj):
        if isinstance(obj, dict):
            return obj.get("image") or obj.get("image_url")
        return getattr(obj, "image_url", None)

    def to_representation(self, instance):
        from django.db import models

        if isinstance(instance, models.Model):
            manga_metadata = getattr(instance, "metadata", {}) or {}
            mapped_instance = {
                "id": getattr(instance, "external_id", None),
                "title": getattr(instance, "title", ""),
                "title_english": getattr(instance, "title_english", None),
                "title_native": getattr(instance, "title_native", None),
                "image": getattr(instance, "image_url", None),
                "media_type": getattr(instance, "media_type", None),
                "year": getattr(instance, "release_year", None),
                "popularity": int(getattr(instance, "popularity", 0) or 0),
                "genres": manga_metadata.get("genres", []),
                "tags": manga_metadata.get("tags", []),
                "micro_tags": manga_metadata.get("micro_tags", []),
                "description": getattr(instance, "description", ""),
                "studios": manga_metadata.get("studios", []),
                "author": manga_metadata.get("author", None),
                "related_items": manga_metadata.get("related_items", []),
            }
            instance = mapped_instance

        # Les résultats pgvector portent `popularity` sous forme de dict imbriqué
        # ({'favourites': N}, issu des métadonnées AniList) alors que le champ
        # sérialiseur attend un entier → on normalise pour éviter un int(dict).
        if isinstance(instance, dict) and isinstance(instance.get("popularity"), dict):
            instance = {
                **instance,
                "popularity": int(instance["popularity"].get("favourites") or 0),
            }

        ret = super().to_representation(instance)
        # Sécurisation des contenus potentiellement générés par l'IA ou utilisateurs
        if ret.get("description"):
            ret["description"] = sanitize_html_content(ret["description"])

        # Sanitisation des listes de tags (même si normalement c'est du texte brut, on est prudent)
        for key in ["tags", "micro_tags", "genres"]:
            if ret.get(key):
                ret[key] = [sanitize_html_content(t) for t in ret[key]]

        return ret


class FavoriteMangaSerializer(serializers.ModelSerializer):
    manga = MediaItemSerializer(read_only=True)
    unread_chapters_count = serializers.SerializerMethodField()

    class Meta:
        model = FavoriteManga
        fields = [
            "id",
            "manga",
            "status",
            "last_read_chapter",
            "unread_chapters_count",
            "created_at",
            "updated_at",
        ]

    def get_unread_chapters_count(self, obj):
        if hasattr(obj, "unread_chapters_count_annotated"):
            return obj.unread_chapters_count_annotated
        return MangaChapter.objects.filter(
            manga=obj.manga, number__gt=obj.last_read_chapter
        ).count()


from .models import Friendship, Notification  # noqa: E402


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"


class FriendshipSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="to_user.username", read_only=True)
    level = serializers.IntegerField(source="to_user.profile.level", read_only=True)

    class Meta:
        model = Friendship
        fields = ["id", "to_user", "username", "level", "created_at"]


class SocialUserSerializer(serializers.ModelSerializer):
    level = serializers.IntegerField(source="profile.level", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "level"]


class CreativeFusionSerializer(serializers.ModelSerializer):
    creator_name = serializers.ReadOnlyField(source="creator.username")
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = CreativeFusion
        fields = "__all__"

    def get_likes_count(self, obj):
        if (
            hasattr(obj, "_prefetched_objects_cache")
            and "likes" in obj._prefetched_objects_cache
        ):
            return len(obj.likes.all())
        return obj.likes.count()

    def get_is_liked(self, obj):
        user = self.context["request"].user if "request" in self.context else None
        if user and user.is_authenticated:
            if (
                hasattr(obj, "_prefetched_objects_cache")
                and "likes" in obj._prefetched_objects_cache
            ):
                return user in obj.likes.all()
            return obj.likes.filter(id=user.id).exists()
        return False


# MarketListingSerializer has been removed


from .models import VsBattle  # noqa: E402


class VsBattleSerializer(serializers.ModelSerializer):
    creator_name = serializers.ReadOnlyField(source="creator.username")
    likes_count = serializers.IntegerField(source="likes.count", read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = VsBattle
        fields = "__all__"

    def get_is_liked(self, obj):
        user = self.context["request"].user if "request" in self.context else None
        if user and user.is_authenticated:
            if (
                hasattr(obj, "_prefetched_objects_cache")
                and "likes" in obj._prefetched_objects_cache
            ):
                return user in obj.likes.all()
            return obj.likes.filter(id=user.id).exists()
        return False


from .models import (  # noqa: E402
    AIFeedback,
    AIREvalResult,
    AISafetyEvent,  # noqa: E402
    GameplaySession,  # noqa: E402
    GoldDatasetEntry,
)


class AISafetyEventSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = AISafetyEvent
        fields = "__all__"


class AIREvalResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIREvalResult
        fields = "__all__"


class GoldDatasetEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = GoldDatasetEntry
        fields = "__all__"


class AIFeedbackSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = AIFeedback
        fields = "__all__"


class GameplaySessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameplaySession
        fields = [
            "id",
            "game_mode",
            "media_type",
            "target_item",
            "history",
            "was_won",
            "created_at",
        ]
        read_only_fields = fields


# --- 🏘️ CLUB SERIALIZERS ---
class ClubMembershipSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = ClubMembership
        fields = ["id", "user", "username", "role", "joined_at"]


class ClubEventSerializer(serializers.ModelSerializer):
    participants_count = serializers.SerializerMethodField()
    is_participant = serializers.SerializerMethodField()

    class Meta:
        model = ClubEvent
        fields = [
            "id",
            "club",
            "title",
            "description",
            "event_date",
            "created_at",
            "participants_count",
            "is_participant",
        ]

    def get_participants_count(self, obj):
        if hasattr(obj, "participants_count_annotated"):
            return obj.participants_count_annotated
        if (
            hasattr(obj, "_prefetched_objects_cache")
            and "participants" in obj._prefetched_objects_cache
        ):
            return len(obj.participants.all())
        return obj.participants.count()

    def get_is_participant(self, obj):
        user = self.context["request"].user if "request" in self.context else None
        if user and user.is_authenticated:
            if (
                hasattr(obj, "_prefetched_objects_cache")
                and "participants" in obj._prefetched_objects_cache
            ):
                return user in obj.participants.all()
            return obj.participants.filter(id=user.id).exists()
        return False


class DiscoveryClubSerializer(serializers.ModelSerializer):
    creator_name = serializers.ReadOnlyField(source="creator.username")
    members_count = serializers.SerializerMethodField()
    events = ClubEventSerializer(many=True, read_only=True)

    class Meta:
        model = DiscoveryClub
        fields = [
            "id",
            "name",
            "description",
            "theme",
            "creator",
            "creator_name",
            "members_count",
            "image_url",
            "is_private",
            "events",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["creator"]

    def get_members_count(self, obj):
        if hasattr(obj, "members_count_annotated"):
            return obj.members_count_annotated
        return obj.members.count()

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if ret.get("description"):
            ret["description"] = sanitize_html_content(ret["description"])
        if ret.get("name"):
            ret["name"] = sanitize_html_content(ret["name"])
        return ret


class GlobalBossSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalBoss
        fields = [
            "id",
            "title",
            "media_type",
            "total_hp",
            "current_hp",
            "community_hints",
            "is_active",
            "start_date",
            "end_date",
            "reward_xp",
            "current_phase",
            "phase_modifiers",
        ]


class BossParticipationSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = BossParticipation
        fields = [
            "id",
            "user",
            "username",
            "points_contributed",
            "best_tier",
            "limiter_breaks",
            "last_participation",
        ]


class DataCurationTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataCurationTicket
        fields = "__all__"


# --- MLOPS SERIALIZERS ---
class AIFeedbackInputSerializer(serializers.Serializer):
    is_positive = serializers.BooleanField()
    type = serializers.CharField(required=False, default="general")
    input_context = serializers.CharField(required=False, allow_blank=True)
    context = serializers.CharField(required=False, allow_blank=True)
    query = serializers.CharField(required=False, allow_blank=True)
    output_text = serializers.CharField(required=False, allow_blank=True)
    output = serializers.CharField(required=False, allow_blank=True)

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        # Gestion des alias/fallbacks
        ret["input_context"] = (
            ret.get("input_context") or ret.get("context") or ret.get("query") or ""
        )
        ret["output_text"] = ret.get("output_text") or ret.get("output") or ""
        return ret


class DPOCurationSerializer(serializers.Serializer):
    feedback_id = serializers.IntegerField()
    chosen_text = serializers.CharField()


# --- GAME SERIALIZERS ---
class ArchetypistFusionSerializer(serializers.Serializer):
    title_A = serializers.CharField(required=False, allow_blank=True)
    title_B = serializers.CharField(required=False, allow_blank=True)
    media_type_A = serializers.CharField(required=False)
    media_type_B = serializers.CharField(required=False)
    chaos_level = serializers.IntegerField(
        required=False, default=50, min_value=0, max_value=100
    )
    universe_balance = serializers.IntegerField(
        required=False, default=50, min_value=0, max_value=100
    )
    art_style = serializers.CharField(required=False, default="Cyberpunk")
    parent_id = serializers.IntegerField(required=False, allow_null=True)


# --- AKINETIX SERIALIZERS ---
class AkinetixStartSerializer(serializers.Serializer):
    media_type = serializers.ChoiceField(
        choices=["Anime", "Manga", "Character"], default="Anime"
    )
    is_daily = serializers.BooleanField(required=False, default=False)


class AkinetixAnswerSerializer(serializers.Serializer):
    answer = serializers.CharField()

    ALLOWED_ANSWERS = [
        "OUI",
        "NON",
        "PROBABLEMENT",
        "PROBABLEMENT PAS",
        "JE NE SAIS PAS",
        # Backward-compat with the old single "maybe" button.
        "PEUT-ÊTRE",
    ]

    def validate_answer(self, value):
        val = value.upper().strip()
        if val == "PEUT-ETRE":
            val = "PEUT-ÊTRE"
        if val not in self.ALLOWED_ANSWERS:
            raise serializers.ValidationError(
                "Réponse invalide : utilisez OUI, NON, PROBABLEMENT, "
                "PROBABLEMENT PAS ou JE NE SAIS PAS."
            )
        return val


class AkinetixConfirmSerializer(serializers.Serializer):
    correct = serializers.BooleanField()
    actual_target = serializers.CharField(required=False, allow_blank=True)


# --- COGNITION SERIALIZERS ---
class AIDebateSerializer(serializers.Serializer):
    media_title = serializers.CharField()
    topic = serializers.CharField()


class CounterfactualSerializer(serializers.Serializer):
    what_if = serializers.CharField()
    actual_context = serializers.ListField(
        child=serializers.DictField(), required=False, default=list
    )


class CoveOracleSerializer(serializers.Serializer):
    question = serializers.CharField()
    media_type = serializers.CharField(required=False, default="anime")


class CFRStrategySerializer(serializers.Serializer):
    questions = serializers.ListField(child=serializers.CharField(), required=False)
    iterations = serializers.IntegerField(
        required=False, default=100, min_value=1, max_value=1000
    )


# --- AUTH SERIALIZERS ---
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class VoiceProfileSerializer(serializers.ModelSerializer):
    sample_url = serializers.ReadOnlyField()

    class Meta:
        model = VoiceProfile
        fields = [
            "id",
            "name",
            "language",
            "origin",
            "definition",
            "roles",
            "impact",
            "origin_detail",
            "sample_url",
            "created_at",
            "updated_at",
        ]
