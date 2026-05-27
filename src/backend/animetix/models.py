from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime

from django.conf import settings

try:
    from pgvector.django import VectorField
except ImportError:
    VectorField = None

# --- 🎭 RELATIONAL CATALOG ---
class MediaItem(models.Model):
    MEDIA_TYPES = [('Anime', 'Anime'), ('Manga', 'Manga'), ('Character', 'Character'), ('Game', 'Video Game'), ('Actor', 'Actor/Actress'), ('Movie', 'Movie')]
    external_id = models.CharField(max_length=100, db_index=True)
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES)
    title = models.CharField(max_length=255)
    title_english = models.CharField(max_length=255, null=True, blank=True)
    title_native = models.CharField(max_length=255, null=True, blank=True)
    synopsis_en = models.TextField(null=True, blank=True)
    synopsis_fr = models.TextField(null=True, blank=True)
    alternative_titles = models.JSONField(default=list)
    description = models.TextField(null=True, blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    release_year = models.IntegerField(null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)
    popularity = models.FloatField(default=0.0)
    
    if VectorField:
        thematic_embedding = VectorField(dimensions=1024, null=True, blank=True)
        plot_embedding = VectorField(dimensions=1024, null=True, blank=True)
        visual_embedding = VectorField(dimensions=512, null=True, blank=True)
    else:
        thematic_embedding = models.JSONField(null=True, blank=True)
        plot_embedding = models.JSONField(null=True, blank=True)
        visual_embedding = models.JSONField(null=True, blank=True)
        
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('external_id', 'media_type')
    def __str__(self): return f"[{self.media_type}] {self.title}"

# --- 👤 USER SYSTEM ---
class Profile(models.Model):
    TIERS = [('free', 'Free'), ('premium', 'Premium'), ('pro', 'Professional')]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    xp = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    max_streak = models.IntegerField(default=0)
    last_win_date = models.DateField(null=True, blank=True)
    total_wins = models.IntegerField(default=0)
    total_games = models.IntegerField(default=0)
    ranked_points = models.IntegerField(default=0) 
    ranked_max_points = models.IntegerField(default=0)
    unlocked_badges = models.JSONField(default=list)
    custom_username_color = models.CharField(max_length=20, null=True, blank=True)
    collected_fusions = models.ManyToManyField('CreativeFusion', related_name='collected_by_profiles', blank=True)
    tier = models.CharField(max_length=20, choices=TIERS, default='free')
    api_key = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    @property
    def level(self): return (self.xp // 500) + 1
    @property
    def level_xp_progress(self): return ((self.xp % 500) / 500) * 100
    @property
    def level_title(self):
        lvl = self.level
        if lvl >= 100: return "Dieu de l'Olympe"
        if lvl >= 50: return "Légende Vivante"
        if lvl >= 30: return "Maître Otaku"
        if lvl >= 20: return "Expert Shonen"
        if lvl >= 10: return "Initié du Dimanche"
        return "Nouveau Né"

    def add_win(self, is_daily=False, is_ranked=False, item_rank=100, game_mode='classic', media_type='Anime', attempts=0):
        from core.domain.services.ranking_service import RankingService
        from adapters.persistence.django_profile_adapter import DjangoProfileAdapter
        from .services import check_achievements
        service = RankingService()
        domain_profile = DjangoProfileAdapter.to_domain(self)
        updated_profile = service.calculate_win(domain_profile, is_daily=is_daily, is_ranked=is_ranked, item_rank=item_rank)
        DjangoProfileAdapter.update_django(self, updated_profile)
        item_rarity = "Legendary" if item_rank > 2000 else "Epic" if item_rank > 1000 else "Rare" if item_rank > 500 else "Common"
        return check_achievements(self.user, 'win', {'game_mode': game_mode, 'media_type': media_type, 'is_daily': is_daily, 'is_ranked': is_ranked, 'attempts': attempts, 'item_rarity': item_rarity})

class Friendship(models.Model):
    from_user = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: unique_together = ('from_user', 'to_user')

# --- 🎮 GAME MODES ---
class GlobalBoss(models.Model):
    title = models.CharField(max_length=255)
    secret_title = models.CharField(max_length=255)
    media_type = models.CharField(max_length=20)
    total_hp = models.IntegerField(default=10000)
    current_hp = models.IntegerField(default=10000)
    community_hints = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    reward_xp = models.IntegerField(default=1000)
    current_phase = models.IntegerField(default=1)
    phase_modifiers = models.JSONField(default=dict)

    def update_phase(self) -> bool:
        old_phase = self.current_phase
        hp_percent = (self.current_hp / self.total_hp) * 100 if self.total_hp > 0 else 0
        if hp_percent < 10: self.current_phase = 3
        elif hp_percent < 50: self.current_phase = 2
        else: self.current_phase = 1
        return old_phase != self.current_phase

class BossParticipation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    boss = models.ForeignKey(GlobalBoss, on_delete=models.CASCADE)
    points_contributed = models.IntegerField(default=0)
    last_participation = models.DateTimeField(auto_now=True)

class DuelRoom(models.Model):
    room_code = models.CharField(max_length=10, unique=True)
    player1 = models.ForeignKey(User, related_name='duels_p1', on_delete=models.CASCADE)
    player2 = models.ForeignKey(User, related_name='duels_p2', on_delete=models.CASCADE, null=True, blank=True)
    media_type = models.CharField(max_length=20)
    secret_title = models.CharField(max_length=255)
    winner = models.ForeignKey(User, related_name='duels_won', on_delete=models.SET_NULL, null=True, blank=True)
    is_finished = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class DailyChallenge(models.Model):
    date = models.DateField(unique=True); media_type = models.CharField(max_length=20); game_mode = models.CharField(max_length=20, default='classic'); secret_title = models.CharField(max_length=255)
class ChallengeResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE); challenge = models.ForeignKey(DailyChallenge, on_delete=models.CASCADE); attempts = models.IntegerField(); time_taken = models.FloatField(default=0.0); completed_at = models.DateTimeField(auto_now_add=True)

# --- 🏆 ACHIEVEMENTS & FEEDBACK ---
class Achievement(models.Model):
    code = models.CharField(max_length=50, unique=True); name = models.CharField(max_length=100); description = models.TextField(); icon = models.CharField(max_length=50); xp_reward = models.IntegerField(default=100); rarity = models.CharField(max_length=20, default="Common")
    def __str__(self): return self.name

class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE); achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE); unlocked_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.user.username} - {self.achievement.name}"

class AIFeedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True); feedback_type = models.CharField(max_length=50); input_context = models.TextField(default=""); output_text = models.TextField(default=""); is_positive = models.BooleanField(); created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Feedback {self.feedback_type}"

class GameplaySession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    game_mode = models.CharField(max_length=50); media_type = models.CharField(max_length=20); target_item = models.CharField(max_length=255); history = models.JSONField(); was_won = models.BooleanField(default=False); created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.game_mode} - {self.target_item}"

class AIREvalResult(models.Model):
    game_mode = models.CharField(max_length=50, default='classic'); input_context = models.TextField(default=""); output_text = models.TextField(default=""); faithfulness = models.FloatField(default=0.0); relevancy = models.FloatField(default=0.0); precision = models.FloatField(default=0.0); hallucination_detected = models.BooleanField(default=False); created_at = models.DateTimeField(auto_now_add=True)

class GoldDatasetEntry(models.Model):
    """Dataset de haute qualité pour le fine-tuning, validé manuellement."""
    context = models.TextField()
    instruction = models.TextField()
    response = models.TextField()
    source_feedback = models.OneToOneField(AIFeedback, on_delete=models.SET_NULL, null=True, blank=True)
    is_validated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Gold Entry {self.id} - {self.instruction[:30]}..."

class SemanticCache(models.Model):
    """Cache sémantique pour les réponses LLM."""
    query_text = models.TextField(unique=True)
    response_text = models.TextField()
    if VectorField:
        query_embedding = VectorField(dimensions=768, null=True, blank=True) # paraphrase-multilingual-mpnet-base-v2
    else:
        query_embedding = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.query_text[:50]

class DataCurationTicket(models.Model):
    """Ticket généré par l'IA autonome pour corriger des contradictions."""
    item_title = models.CharField(max_length=255)
    issue_description = models.TextField()
    source_pg = models.JSONField(default=dict)
    source_neo4j = models.JSONField(default=dict)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Ticket {self.id}: {self.item_title}"

class AITokenUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    engine = models.CharField(max_length=50)
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    cost_estimate = models.FloatField(default=0.0) # In USD or native currency
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.engine} usage by {self.user.username if self.user else 'Guest'}"

class Donation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.FloatField()
    currency = models.CharField(max_length=10, default="USD")
    platform = models.CharField(max_length=50) # Ko-fi, Patreon, etc.
    transaction_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Donation of {self.amount} {self.currency} by {self.user.username if self.user else 'Anonymous'}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created: Profile.objects.create(user=instance)
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class LatentSpacePoint(models.Model):
    """Point de données dans l'espace latent pour la visualisation 3D."""
    media_type = models.CharField(max_length=20) # anime, manga, character
    vibe_type = models.CharField(max_length=20) # thematic, visual, scenario
    external_id = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    x = models.FloatField()
    y = models.FloatField()
    z = models.FloatField()
    cluster = models.IntegerField(default=0)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('media_type', 'vibe_type', 'external_id')
        indexes = [
            models.Index(fields=['media_type', 'vibe_type']),
        ]
    def __str__(self): return f"{self.media_type} - {self.vibe_type} - {self.title}"

class CreativeFusion(models.Model):
    title_a = models.CharField(max_length=255)
    title_b = models.CharField(max_length=255)
    media_type_a = models.CharField(max_length=50)
    media_type_b = models.CharField(max_length=50)
    
    scenario_text = models.TextField()
    image_url = models.URLField(max_length=500, null=True, blank=True)
    
    chaos_level = models.IntegerField(default=50)
    universe_balance = models.IntegerField(default=50)
    art_style = models.CharField(max_length=100, default='Cyberpunk')
    
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='fusions')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='remixes')
    likes = models.ManyToManyField(User, related_name='liked_fusions', blank=True)
    vn_script = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)    
    def __str__(self):
        return f"{self.title_a} x {self.title_b} by {self.creator}"

class Notification(models.Model):
    TYPES = [
        ('achievement', 'Succès Débloqué'),
        ('duel', 'Défi / Duel'),
        ('social', 'Interaction Sociale'),
        ('system', 'Système'),
        ('info', 'Information')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPES, default='info')
    link = models.CharField(max_length=500, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title} ({self.notification_type})"
