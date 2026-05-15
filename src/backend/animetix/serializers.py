from rest_framework import serializers
from .models import Profile, DailyChallenge, ChallengeResult, Achievement, UserAchievement
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
            'user', 'xp', 'current_streak', 'max_streak', 
            'total_wins', 'total_games', 'ranked_points', 
            'ranked_max_points', 'rank'
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
    title_english = serializers.CharField(required=False)
    title_native = serializers.CharField(required=False)
    image = serializers.URLField(required=False)
    year = serializers.IntegerField(required=False)
    popularity = serializers.IntegerField(required=False)
    genres = serializers.ListField(child=serializers.CharField(), required=False)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    description = serializers.CharField(required=False)
