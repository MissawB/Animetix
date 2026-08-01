from django.contrib.auth.models import User
from django.db import models

from .catalog import MangaChapter, MediaItem


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


class MangaReadingProgress(models.Model):
    """Progression de lecture d'un chapitre, par utilisateur.

    La vérité vit ici et non dans Suwayomi : l'état de Suwayomi est global au
    serveur (mono-utilisateur) et injoignable en production. Suwayomi n'en
    reçoit qu'un miroir best-effort.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="manga_progress"
    )
    chapter = models.ForeignKey(
        MangaChapter, on_delete=models.CASCADE, related_name="progress"
    )
    # Index 0-based, comme `lastPageRead` de Suwayomi et `currentPageIndex` du lecteur.
    last_page_read = models.IntegerField(default=0)
    is_read = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Couvre aussi la recherche « progression de cet utilisateur sur ce chapitre ».
        unique_together = ("user", "chapter")

    def __str__(self):
        return f"{self.user.username} - {self.chapter} - p{self.last_page_read}"
