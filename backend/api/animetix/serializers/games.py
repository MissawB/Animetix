from rest_framework import serializers

from ..models import (
    Achievement,
    BossParticipation,
    CreativeFusion,
    DailyChallenge,
    GameplaySession,
    GlobalBoss,
    VsBattle,
)


class DailyChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyChallenge
        fields = "__all__"


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = "__all__"


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


class CreativeFusionSerializer(serializers.ModelSerializer):
    creator_name = serializers.ReadOnlyField(source="creator.username")
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = CreativeFusion
        fields = [
            "id",
            "title_a",
            "title_b",
            "media_type_a",
            "media_type_b",
            "scenario_text",
            "image_url",
            "chaos_level",
            "universe_balance",
            "art_style",
            "creator",
            "creator_name",
            "parent",
            "vn_script",
            "is_public",
            "created_at",
            "likes_count",
            "is_liked",
        ]

    def get_likes_count(self, obj) -> int:
        if hasattr(obj, "likes_count"):
            return obj.likes_count
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


class VsBattleSerializer(serializers.ModelSerializer):
    creator_name = serializers.ReadOnlyField(source="creator.username")
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = VsBattle
        fields = [
            "id",
            "char_a_name",
            "char_b_name",
            "char_a_franchise",
            "char_b_franchise",
            "char_a_data",
            "char_b_data",
            "winner",
            "verdict_summary",
            "debate_history",
            "creator",
            "creator_name",
            "is_public",
            "created_at",
            "likes_count",
            "is_liked",
        ]

    def get_likes_count(self, obj) -> int:
        if hasattr(obj, "likes_count"):
            return obj.likes_count
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
