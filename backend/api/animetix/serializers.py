from rest_framework import serializers
from .models import Profile, DailyChallenge, ChallengeResult, Achievement, UserAchievement, CreativeFusion, DiscoveryClub, ClubMembership, ClubEvent
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    rank = serializers.ReadOnlyField()
    
    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'xp', 'current_streak', 'max_streak', 
            'last_win_date', 'total_wins', 'total_games', 'ranked_points', 
            'ranked_max_points', 'rank', 'unlocked_badges', 
            'custom_username_color', 'tier'
        ]

class DailyChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyChallenge
        fields = '__all__'

class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = '__all__'

# Serializers pour les données chargées dynamiquement (JSON/Chroma)
class MediaItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    title_english = serializers.CharField(required=False, allow_null=True)
    title_native = serializers.CharField(required=False, allow_null=True)
    image = serializers.URLField(required=False, allow_null=True)
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

from .models import Friendship, Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

class FriendshipSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='to_user.username', read_only=True)
    level = serializers.IntegerField(source='to_user.profile.level', read_only=True)

    class Meta:
        model = Friendship
        fields = ['id', 'to_user', 'username', 'level', 'created_at']

class SocialUserSerializer(serializers.ModelSerializer):
    level = serializers.IntegerField(source='profile.level', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'level']

class CreativeFusionSerializer(serializers.ModelSerializer):
    creator_name = serializers.ReadOnlyField(source='creator.username')
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)
    is_remix = serializers.SerializerMethodField()

    class Meta:
        model = CreativeFusion
        fields = '__all__'

from .models import AIREvalResult, GoldDatasetEntry, AIFeedback

class AIREvalResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIREvalResult
        fields = '__all__'

class GoldDatasetEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = GoldDatasetEntry
        fields = '__all__'

class AIFeedbackSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = AIFeedback
        fields = '__all__'

# --- 🏘️ CLUB SERIALIZERS ---
class ClubMembershipSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = ClubMembership
        fields = ['id', 'user', 'username', 'role', 'joined_at']

class ClubEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubEvent
        fields = '__all__'

class DiscoveryClubSerializer(serializers.ModelSerializer):
    creator_name = serializers.ReadOnlyField(source='creator.username')
    members_count = serializers.IntegerField(source='members.count', read_only=True)
    events = ClubEventSerializer(many=True, read_only=True)
    
    class Meta:
        model = DiscoveryClub
        fields = [
            'id', 'name', 'description', 'theme', 'creator', 'creator_name', 
            'members_count', 'image_url', 'is_private', 'events', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['creator']
