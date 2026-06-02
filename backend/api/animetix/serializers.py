from rest_framework import serializers
from .models import Profile, DailyChallenge, ChallengeResult, Achievement, UserAchievement, CreativeFusion, DiscoveryClub, ClubMembership, ClubEvent, GlobalBoss, BossParticipation, DataCurationTicket
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    rank = serializers.ReadOnlyField()
    has_api_key = serializers.SerializerMethodField()
    
    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'xp', 'current_streak', 'max_streak', 
            'last_win_date', 'total_wins', 'total_games', 'ranked_points', 
            'ranked_max_points', 'rank', 'unlocked_badges', 
            'custom_username_color', 'tier', 'personalization_settings',
            'has_api_key'
        ]

    def get_has_api_key(self, obj):
        return bool(obj.api_key_hash)

class DailyChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyChallenge
        fields = '__all__'

class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = '__all__'

from core.utils.security import sanitize_html_content

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

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Sécurisation des contenus potentiellement générés par l'IA ou utilisateurs
        if ret.get('description'):
            ret['description'] = sanitize_html_content(ret['description'])
        
        # Sanitisation des listes de tags (même si normalement c'est du texte brut, on est prudent)
        for key in ['tags', 'micro_tags', 'genres']:
            if ret.get(key):
                ret[key] = [sanitize_html_content(t) for t in ret[key]]
                
        return ret

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
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = CreativeFusion
        fields = '__all__'
    
    def get_is_liked(self, obj):
        user = self.context['request'].user if 'request' in self.context else None
        if user and user.is_authenticated:
            return obj.likes.filter(id=user.id).exists()
        return False

from .models import VsBattle

class VsBattleSerializer(serializers.ModelSerializer):
    creator_name = serializers.ReadOnlyField(source='creator.username')
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = VsBattle
        fields = '__all__'
    
    def get_is_liked(self, obj):
        user = self.context['request'].user if 'request' in self.context else None
        if user and user.is_authenticated:
            return obj.likes.filter(id=user.id).exists()
        return False

from .models import (
    AIREvalResult, 
    GoldDatasetEntry, 
    AIFeedback,
    GameplaySession
)

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

class GameplaySessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameplaySession
        fields = ['id', 'game_mode', 'media_type', 'target_item', 'history', 'was_won', 'created_at']
        read_only_fields = fields

# --- 🏘️ CLUB SERIALIZERS ---
class ClubMembershipSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = ClubMembership
        fields = ['id', 'user', 'username', 'role', 'joined_at']

class ClubEventSerializer(serializers.ModelSerializer):
    participants_count = serializers.IntegerField(source='participants.count', read_only=True)
    is_participant = serializers.SerializerMethodField()

    class Meta:
        model = ClubEvent
        fields = ['id', 'club', 'title', 'description', 'event_date', 'created_at', 'participants_count', 'is_participant']
    
    def get_is_participant(self, obj):
        user = self.context['request'].user if 'request' in self.context else None
        if user and user.is_authenticated:
            return obj.participants.filter(id=user.id).exists()
        return False

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

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if ret.get('description'):
            ret['description'] = sanitize_html_content(ret['description'])
        if ret.get('name'):
            ret['name'] = sanitize_html_content(ret['name'])
        return ret

class GlobalBossSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalBoss
        fields = [
            'id', 'title', 'media_type', 'total_hp', 'current_hp', 
            'community_hints', 'is_active', 'start_date', 'end_date', 
            'reward_xp', 'current_phase', 'phase_modifiers'
        ]

class BossParticipationSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = BossParticipation
        fields = ['id', 'user', 'username', 'points_contributed', 'last_participation']

class DataCurationTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataCurationTicket
        fields = '__all__'
