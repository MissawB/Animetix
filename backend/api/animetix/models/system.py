from django.contrib.auth.models import User
from django.db import models


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


class SiteConfiguration(models.Model):
    maintenance_mode = models.BooleanField(
        default=False,
        help_text="ON : les visiteurs voient la page de maintenance ; le staff navigue normalement.",
    )
    maintenance_message = models.TextField(
        blank=True,
        default="",
        help_text="Message optionnel affiché sur la page de maintenance.",
    )
    maintenance_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Heure de retour estimée (informatif, affiché sur la page).",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuration du site"
        verbose_name_plural = "Configuration du site"

    def __str__(self):
        return "Configuration du site"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls) -> "SiteConfiguration":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
