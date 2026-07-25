from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from django.db import models


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
    # Photo de profil : FileField (pas d'ImageField → pas de dépendance Pillow).
    # Stockée via l'infra média (GCS en prod, MEDIA_ROOT en dev).
    avatar = models.FileField(upload_to="avatars/", null=True, blank=True)
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
    def rank(self):
        from core.domain.entities.user import rank_label_for  # noqa: E402

        return rank_label_for(self.ranked_points)

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

        from ..services import check_achievements  # noqa: E402

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
