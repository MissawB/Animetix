from django.contrib.auth.models import User
from django.db import models

from .catalog import MediaItem


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


class MangaCover(models.Model):
    manga_id = models.CharField(max_length=50, unique=True, db_index=True)
    title = models.CharField(max_length=255)
    mangadex_id = models.CharField(max_length=100, null=True, blank=True)
    covers = models.JSONField(default=dict)  # format: {"ja": [...], "fr": [...]}
    title_english = models.CharField(max_length=255, null=True, blank=True)
    title_native = models.CharField(max_length=255, null=True, blank=True)
    synonyms = models.JSONField(default=list, null=True, blank=True)
    author = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = "Manga Cover"
        verbose_name_plural = "Manga Covers"

    def __str__(self):
        return self.title
