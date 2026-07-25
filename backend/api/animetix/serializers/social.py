from core.utils.security import sanitize_html_content
from django.contrib.auth.models import User
from rest_framework import serializers

from ..models import (
    ClubEvent,
    ClubMembership,
    DiscoveryClub,
    Friendship,
    Notification,
    Profile,
    TrackerConnection,
)


class TrackerConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackerConnection
        fields = ["id", "tracker", "username", "created_at"]


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
    avatar = serializers.SerializerMethodField()

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
            "avatar",
            "tier",
            "wallet_balance",
            "personalization_settings",
            "has_api_key",
        ]

    def get_has_api_key(self, obj):
        return bool(obj.api_key_hash)

    def get_avatar(self, obj):
        if not obj.avatar:
            return None
        url = obj.avatar.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url


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

    def get_participants_count(self, obj) -> int:
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

    def get_members_count(self, obj) -> int:
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


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
