from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


# --- RELATIONAL CATALOG ---
class MediaItem(models.Model):
    MEDIA_TYPES = [
        ("Anime", "Anime"),
        ("Manga", "Manga"),
        ("Character", "Character"),
        ("Game", "Video Game"),
        ("Actor", "Actor/Actress"),
        ("Movie", "Movie"),
    ]
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

    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("external_id", "media_type")

    def __str__(self):
        return f"[{self.media_type}] {self.title}"


class MangaChapter(models.Model):
    manga = models.ForeignKey(
        MediaItem,
        on_delete=models.CASCADE,
        related_name="chapters",
        limit_choices_to={"media_type": "Manga"},
    )
    number = models.FloatField()
    title = models.CharField(max_length=255, null=True, blank=True)
    external_id = models.CharField(max_length=100, db_index=True, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["number"]
        unique_together = ("manga", "number")

    def __str__(self):
        return f"{self.manga.title} - Ch.{self.number}"


class MangaPage(models.Model):
    chapter = models.ForeignKey(
        MangaChapter, on_delete=models.CASCADE, related_name="pages"
    )
    number = models.IntegerField()
    image_url = models.URLField(max_length=500)

    # Metadata for potential OCR/Translation data
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["number"]
        unique_together = ("chapter", "number")

    def __str__(self):
        return f"{self.chapter} - Page {self.number}"


class FavoriteManga(models.Model):
    STATUS_CHOICES = [
        ("reading", "Reading"),
        ("completed", "Completed"),
        ("plan_to_read", "Plan to Read"),
    ]
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="favorite_mangas"
    )
    manga = models.ForeignKey(
        MediaItem,
        on_delete=models.CASCADE,
        related_name="favorited_by",
        limit_choices_to={"media_type": "Manga"},
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="reading",
    )
    last_read_chapter = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "manga")

    def __str__(self):
        return f"{self.user.username} - {self.manga.title}"


class TrackerConnection(models.Model):
    TRACKER_CHOICES = [
        ("myanimelist", "MyAnimeList"),
        ("anilist", "AniList"),
    ]
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="tracker_connections"
    )
    tracker = models.CharField(max_length=20, choices=TRACKER_CHOICES)
    token = models.TextField(blank=True, null=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "tracker")

    def __str__(self):
        return f"{self.user.username} - {self.tracker} ({self.username or 'Connected'})"


# --- USER SYSTEM ---
class Profile(models.Model):
    TIERS = [("free", "Free"), ("premium", "Premium"), ("pro", "Professional")]
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
    tier = models.CharField(max_length=20, choices=TIERS, default="free")
    wallet_balance = models.IntegerField(default=1000)
    api_key_hash = models.CharField(max_length=255, unique=True, null=True, blank=True)
    personalization_settings = models.JSONField(default=dict, blank=True)

    def set_api_key(self, raw_key: str):
        """Hashes the raw API key and stores it."""
        self.api_key_hash = make_password(raw_key)

    def check_api_key(self, raw_key: str) -> bool:
        """Verifies a raw API key against the stored hash."""
        if not self.api_key_hash:
            return False
        return check_password(raw_key, self.api_key_hash)

    @property
    def level(self):
        return (self.xp // 500) + 1

    @property
    def level_xp_progress(self):
        return ((self.xp % 500) / 500) * 100

    @property
    def level_title(self):
        lvl = self.level
        if lvl >= 100:
            return "Dieu de l'Olympe"
        if lvl >= 50:
            return "Légende Vivante"
        if lvl >= 30:
            return "Maître Otaku"
        if lvl >= 20:
            return "Expert Shonen"
        if lvl >= 10:
            return "Initié du Dimanche"
        return "Nouveau Né"

    def add_win(
        self,
        is_daily=False,
        is_ranked=False,
        item_rank=100,
        game_mode="classic",
        media_type="Anime",
        attempts=0,
    ):
        from adapters.persistence.django_profile_adapter import (  # noqa: E402
            DjangoProfileAdapter,
        )
        from core.domain.services.ranking_service import RankingService  # noqa: E402

        from .services import check_achievements  # noqa: E402

        service = RankingService()
        domain_profile = DjangoProfileAdapter.to_domain(self)
        updated_profile = service.calculate_win(
            domain_profile, is_daily=is_daily, is_ranked=is_ranked, item_rank=item_rank
        )
        DjangoProfileAdapter.update_django(self, updated_profile)
        item_rarity = (
            "Legendary"
            if item_rank > 2000
            else "Epic" if item_rank > 1000 else "Rare" if item_rank > 500 else "Common"
        )
        return check_achievements(
            self.user,
            "win",
            {
                "game_mode": game_mode,
                "media_type": media_type,
                "is_daily": is_daily,
                "is_ranked": is_ranked,
                "attempts": attempts,
                "item_rarity": item_rarity,
            },
        )


class Friendship(models.Model):
    from_user = models.ForeignKey(
        User, related_name="following", on_delete=models.CASCADE
    )
    to_user = models.ForeignKey(
        User, related_name="followers", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("from_user", "to_user")


# --- GAME MODES ---
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
    reward_distributed = models.BooleanField(default=False)
    current_phase = models.IntegerField(default=1)
    phase_modifiers = models.JSONField(default=dict)

    def update_phase(self) -> bool:
        old_phase = self.current_phase
        hp_percent = (self.current_hp / self.total_hp) * 100 if self.total_hp > 0 else 0
        if hp_percent < 10:
            self.current_phase = 3
        elif hp_percent < 50:
            self.current_phase = 2
        else:
            self.current_phase = 1
        return old_phase != self.current_phase


class BossParticipation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    boss = models.ForeignKey(GlobalBoss, on_delete=models.CASCADE)
    points_contributed = models.IntegerField(default=0)
    last_participation = models.DateTimeField(auto_now=True)


class DuelRoom(models.Model):
    room_code = models.CharField(max_length=10, unique=True)
    player1 = models.ForeignKey(User, related_name="duels_p1", on_delete=models.CASCADE)
    player2 = models.ForeignKey(
        User, related_name="duels_p2", on_delete=models.CASCADE, null=True, blank=True
    )
    media_type = models.CharField(max_length=20)
    secret_title = models.CharField(max_length=255)
    winner = models.ForeignKey(
        User, related_name="duels_won", on_delete=models.SET_NULL, null=True, blank=True
    )
    is_finished = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class DailyChallenge(models.Model):
    date = models.DateField(unique=True)
    media_type = models.CharField(max_length=20)
    game_mode = models.CharField(max_length=20, default="classic")
    secret_title = models.CharField(max_length=255)


class ChallengeResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey(DailyChallenge, on_delete=models.CASCADE)
    attempts = models.IntegerField()
    time_taken = models.FloatField(default=0.0)
    completed_at = models.DateTimeField(auto_now_add=True)


class DailyResult(models.Model):
    """Best daily-challenge score per user, date and universe (anime/manga/character).

    Independent of DailyChallenge (which is single-universe): the daily page now
    offers one target per media type, and past dates are replayable.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="daily_results"
    )
    date = models.DateField()
    media_type = models.CharField(max_length=20)
    score = models.IntegerField(default=0)
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "date", "media_type")


# --- ACHIEVEMENTS & FEEDBACK ---
class Achievement(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50)
    xp_reward = models.IntegerField(default=100)
    rarity = models.CharField(max_length=20, default="Common")

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"


class AIFeedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    feedback_type = models.CharField(max_length=50)
    input_context = models.TextField(default="")
    output_text = models.TextField(default="")
    is_positive = models.BooleanField()
    is_ignored = models.BooleanField(default=False)
    weight = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback {self.feedback_type} ({'IGNORED' if self.is_ignored else 'ACTIVE'})"


class GameplaySession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    game_mode = models.CharField(max_length=50)
    media_type = models.CharField(max_length=20)
    target_item = models.CharField(max_length=255)
    history = models.JSONField()
    was_won = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.game_mode} - {self.target_item}"


class AIREvalResult(models.Model):
    game_mode = models.CharField(max_length=50, default="classic")
    input_context = models.TextField(default="")
    output_text = models.TextField(default="")
    faithfulness = models.FloatField(default=0.0)
    relevancy = models.FloatField(default=0.0)
    precision = models.FloatField(default=0.0)
    hallucination_detected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class GoldDatasetEntry(models.Model):
    """Dataset de haute qualité pour le fine-tuning, validé manuellement."""

    ENTRY_TYPES = [
        ("QA", "Question-Answering"),
        ("MULTIVERSE", "Synthetic Universe"),
        ("DISTILLATION", "Model Distillation"),
        ("OTHER", "Other Synthetic Data"),
    ]

    context = models.TextField()
    instruction = models.TextField()
    response = models.TextField()

    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES, default="QA")
    metadata = models.JSONField(default=dict, blank=True)

    source_feedback = models.OneToOneField(
        AIFeedback, on_delete=models.SET_NULL, null=True, blank=True
    )
    is_validated = models.BooleanField(default=False)

    # AI Validation Fields (HITL Gate)
    ai_validation_score = models.FloatField(default=0.0)
    ai_critique = models.TextField(null=True, blank=True)
    confidence_score = models.FloatField(default=0.0)
    is_safe = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Gold Entry {self.id} ({self.entry_type}) - {self.instruction[:30]}..."


class AISafetyEvent(models.Model):
    """Journal des événements de sécurité LLM (Guardrail)."""

    EVENT_TYPES = [
        ("input", "Entrée Utilisateur"),
        ("output", "Sortie Assistant"),
        ("system", "Système"),
    ]
    ACTIONS = [
        ("block", "Bloqué"),
        ("warn", "Avertissement"),
        ("rewrite", "Réécriture"),
        ("none", "Aucune"),
    ]

    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    action = models.CharField(max_length=20, choices=ACTIONS)
    detected_categories = models.JSONField(default=list)

    input_text = models.TextField(null=True, blank=True)
    output_text = models.TextField(null=True, blank=True)
    reasoning = models.TextField(null=True, blank=True)

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Safety {self.event_type} - {self.action} ({self.created_at})"


class DriftBaseline(models.Model):
    """Référence de détection de dérive d'une collection vectorielle.

    On ne stocke que les NORMES des embeddings (tableau 1D) : le test KS de
    dérive ne compare que ces distributions, donc quelques Ko suffisent — et
    la base étant partagée, la baseline est visible de toutes les instances
    (contrairement à un fichier local éphémère sur Cloud Run)."""

    collection_name = models.CharField(max_length=50, unique=True)
    norms = models.JSONField(default=list)
    sample_size = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"DriftBaseline {self.collection_name} ({self.sample_size} vecteurs)"


class SemanticCache(models.Model):
    """Cache sémantique pour les réponses LLM."""

    query_text = models.TextField(unique=True)
    response_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.query_text[:50]


class DataCurationTicket(models.Model):
    """Ticket généré par l'IA autonome pour corriger des contradictions."""

    item_title = models.CharField(max_length=255)
    issue_description = models.TextField()
    source_pg = models.JSONField(default=dict)
    source_neo4j = models.JSONField(default=dict)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket {self.id}: {self.item_title}"


class AITokenUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    engine = models.CharField(max_length=50)
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    allocated_budget = models.IntegerField(default=0)
    cost_estimate = models.FloatField(default=0.0)  # In USD or native currency
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.engine} usage by {self.user.username if self.user else 'Guest'}"


class AdEvent(models.Model):
    EVENT_TYPES = [("impression", "Impression"), ("click", "Click")]
    AD_TYPES = [("video", "Video"), ("banner", "Banner")]

    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    ad_type = models.CharField(max_length=20, choices=AD_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ad_type} {self.event_type} at {self.created_at}"


class WalletTransaction(models.Model):
    TRANSACTION_TYPES = [
        ("ad_passive", "Passive Mining"),
        ("ad_active", "Rewarded Video"),
        ("purchase", "Direct Purchase"),
        ("ai_usage", "AI Consumption"),
        ("daily_grant", "Daily Grant"),
        ("welcome_bonus", "Welcome Bonus"),
    ]
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="wallet_transactions"
    )
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} ({self.amount})"


# --- ACHIEVEMENTS & FEEDBACK ---


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class LatentSpacePoint(models.Model):
    """Point de données dans l'espace latent pour la visualisation 3D."""

    media_type = models.CharField(max_length=20)  # anime, manga, character
    vibe_type = models.CharField(max_length=20)  # thematic, visual, scenario
    external_id = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    x = models.FloatField()
    y = models.FloatField()
    z = models.FloatField()
    cluster = models.IntegerField(default=0)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("media_type", "vibe_type", "external_id")
        indexes = [
            models.Index(fields=["media_type", "vibe_type"]),
        ]

    def __str__(self):
        return f"{self.media_type} - {self.vibe_type} - {self.title}"


class CreativeFusion(models.Model):
    title_a = models.CharField(max_length=255)
    title_b = models.CharField(max_length=255)
    media_type_a = models.CharField(max_length=50)
    media_type_b = models.CharField(max_length=50)

    scenario_text = models.TextField()
    image_url = models.URLField(max_length=500, null=True, blank=True)

    chaos_level = models.IntegerField(default=50)
    universe_balance = models.IntegerField(default=50)
    art_style = models.CharField(max_length=100, default="Cyberpunk")

    creator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="fusions"
    )
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="remixes"
    )
    likes = models.ManyToManyField(User, related_name="liked_fusions", blank=True)
    vn_script = models.JSONField(null=True, blank=True)
    is_public = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title_a} x {self.title_b} by {self.creator}"


# MarketListing model has been removed


class VsBattle(models.Model):
    char_a_name = models.CharField(max_length=255)
    char_b_name = models.CharField(max_length=255)
    char_a_franchise = models.CharField(max_length=255, null=True, blank=True)
    char_b_franchise = models.CharField(max_length=255, null=True, blank=True)

    char_a_data = models.JSONField()
    char_b_data = models.JSONField()

    winner = models.CharField(max_length=255)
    verdict_summary = models.TextField()
    debate_history = models.JSONField()

    creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vs_battles",
    )
    likes = models.ManyToManyField(User, related_name="liked_vs_battles", blank=True)

    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.char_a_name} vs {self.char_b_name}"


class Notification(models.Model):
    TYPES = [
        ("achievement", "Succès Débloqué"),
        ("duel", "Défi / Duel"),
        ("social", "Interaction Sociale"),
        ("system", "Système"),
        ("info", "Information"),
    ]
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPES, default="info")
    link = models.CharField(max_length=500, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.title} ({self.notification_type})"


# --- CLUBS & SOCIAL GROUPS ---
class DiscoveryClub(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    theme = models.CharField(max_length=50, default="General")
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_clubs"
    )
    members = models.ManyToManyField(
        User, through="ClubMembership", related_name="joined_clubs"
    )
    image_url = models.URLField(max_length=500, null=True, blank=True)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ClubMembership(models.Model):
    ROLES = [("Member", "Member"), ("Officer", "Officer")]
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="club_memberships"
    )
    club = models.ForeignKey(
        DiscoveryClub, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=20, choices=ROLES, default="Member")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "club")


class ArchetypeDriftSnapshot(models.Model):
    """Snapshot historique du profil cognitif de l'utilisateur."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="archetype_snapshots"
    )
    archetype_id = models.CharField(max_length=100)
    intensity = models.FloatField()

    # Statistiques cognitives au moment du snapshot
    shonen_affinity = models.FloatField()
    seinen_affinity = models.FloatField()
    logic_consistency = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.archetype_id} ({self.created_at.date()})"


class ClubEvent(models.Model):
    club = models.ForeignKey(
        DiscoveryClub, on_delete=models.CASCADE, related_name="events"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_date = models.DateTimeField()
    participants = models.ManyToManyField(
        User, related_name="event_participations", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.club.name} - {self.title}"


import json  # noqa: E402


class PGVectorField(models.Field):
    description = "Vector representation compatible with pgvector (PostgreSQL) and JSON strings (SQLite)"

    def db_type(self, connection):
        if connection.vendor == "postgresql":
            return "vector"
        return "text"

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    def to_python(self, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    def get_prep_value(self, value):
        if value is None:
            return value
        if isinstance(value, list):
            return "[" + ",".join(map(str, value)) + "]"
        return value


class VectorRecord(models.Model):
    collection_name = models.CharField(max_length=100, db_index=True)
    item_id = models.CharField(max_length=100, db_index=True)
    embedding = PGVectorField()
    metadata = models.JSONField(default=dict, blank=True)
    document = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("collection_name", "item_id")
        indexes = [
            models.Index(fields=["collection_name", "item_id"]),
        ]

    def __str__(self):
        return f"{self.collection_name} - {self.item_id}"


class UserRecommendation(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recommendations"
    )
    media_item = models.ForeignKey(MediaItem, on_delete=models.CASCADE)
    score = models.FloatField()
    rank = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["rank"]
        unique_together = ("user", "media_item")

    def __str__(self):
        return (
            f"Rec for {self.user.username}: {self.media_item.title} (Rank {self.rank})"
        )


class SupportTicket(models.Model):
    """Ticket de support technique assisté par IA."""

    STATUS_CHOICES = [("open", "Ouvert"), ("resolved", "Résolu"), ("closed", "Fermé")]
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="support_tickets"
    )
    subject = models.CharField(max_length=255)
    query = models.TextField()
    ai_response = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    feedback_score = models.IntegerField(
        null=True, blank=True
    )  # 1 pour Positif, 0 pour Négatif
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket {self.id}: {self.subject}"


class VoiceProfile(models.Model):
    ORIGIN_CHOICES = [
        ("dataset", "Dataset (Hugging Face)"),
        ("youtube", "YouTube Ingestion"),
        ("upload", "Manual Upload"),
    ]
    LANGUAGE_CHOICES = [
        ("japanese", "Japanese (Seiyuu)"),
        ("french", "French (Doubleur)"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=255, unique=True)
    language = models.CharField(
        max_length=20, choices=LANGUAGE_CHOICES, default="japanese"
    )
    origin = models.CharField(max_length=20, choices=ORIGIN_CHOICES, default="dataset")
    definition = models.TextField(null=True, blank=True)
    roles = models.TextField(null=True, blank=True)
    impact = models.CharField(max_length=100, null=True, blank=True)
    origin_detail = models.CharField(
        max_length=500, null=True, blank=True
    )  # HF path or YT URL
    sample_file = models.FileField(upload_to="audio/samples/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_language_display()})"

    @property
    def sample_url(self) -> str:
        if self.sample_file:
            return self.sample_file.url
        if self.origin_detail and self.origin_detail.startswith("http"):
            try:
                from core.utils.security import safe_http_request
                from django.core.files.base import ContentFile
                from django.utils.text import slugify

                response = safe_http_request("GET", self.origin_detail, timeout=10)
                if response.status_code == 200:
                    file_name = f"{slugify(self.name)}_sample.wav"
                    self.sample_file.save(
                        file_name, ContentFile(response.content), save=True
                    )
                    return self.sample_file.url
            except Exception as e:
                import logging

                logging.getLogger("animetix.models").warning(
                    f"Failed to fetch/save voice sample from {self.origin_detail}: {e}"
                )
            return self.origin_detail
        return ""
