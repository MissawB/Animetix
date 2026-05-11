from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    xp = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    max_streak = models.IntegerField(default=0)
    last_win_date = models.DateField(null=True, blank=True)
    total_wins = models.IntegerField(default=0)
    total_games = models.IntegerField(default=0)
    
    # Mode Ranked (Système de Points Linéaire)
    ranked_points = models.IntegerField(default=0) 
    ranked_max_points = models.IntegerField(default=0)
    
    @property
    def rank(self):
        if self.ranked_points < 500: return "Bronze 🥉"
        if self.ranked_points < 1500: return "Argent 🥈"
        if self.ranked_points < 3000: return "Or 🥇"
        if self.ranked_points < 6000: return "Platine 💎"
        if self.ranked_points < 10000: return "Diamant 💠"
        return "Maître de la Data 👑"

    def add_win(self, is_daily=False, is_ranked=False, item_rank=100):
        self.total_wins += 1
        self.total_games += 1
        
        xp_gain = 50
        if is_daily: xp_gain = 150
        
        if is_ranked:
            point_gain = max(10, int(item_rank / 5))
            self.ranked_points += point_gain
            xp_gain = point_gain * 2
            if self.ranked_points > self.ranked_max_points:
                self.ranked_max_points = self.ranked_points
        
        self.xp += xp_gain
        today = datetime.date.today()
        if self.last_win_date == today - datetime.timedelta(days=1):
            self.current_streak += 1
        elif self.last_win_date != today:
            self.current_streak = 1
            
        if self.current_streak > self.max_streak:
            self.max_streak = self.current_streak
        self.last_win_date = today
        self.save()

class DailyChallenge(models.Model):
    date = models.DateField(unique=True)
    media_type = models.CharField(max_length=20)
    game_mode = models.CharField(max_length=20, default='classic')
    secret_title = models.CharField(max_length=255)

class ChallengeResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey(DailyChallenge, on_delete=models.CASCADE)
    attempts = models.IntegerField()
    time_taken = models.FloatField(default=0.0)
    completed_at = models.DateTimeField(auto_now_add=True)

class Achievement(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50)
    xp_reward = models.IntegerField(default=100)
    rarity = models.CharField(max_length=20, default="Common")

class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

class AIFeedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    feedback_type = models.CharField(max_length=50) # 'similarity', 'fusion', 'paradox'
    input_context = models.TextField() 
    output_text = models.TextField()
    is_positive = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

class GameplaySession(models.Model):
    game_mode = models.CharField(max_length=50) # 'animinator', 'akinetix', 'classic'
    media_type = models.CharField(max_length=20)
    target_item = models.CharField(max_length=255)
    history = models.JSONField() # Liste des Q/R : [{"q": "...", "a": "..."}]
    was_won = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created: Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
