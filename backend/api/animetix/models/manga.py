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


class MangaTrackerLink(models.Model):
    """Liaison entre une œuvre du catalogue et son entrée chez un tracker tiers.

    Remplace la résolution par titre faite à chaque poussée, qui mettait
    silencieusement à jour la mauvaise œuvre sur un titre ambigu. `remote_progress`
    mémorise la dernière valeur distante connue pour ne jamais la faire reculer.
    """

    STATUS_CHOICES = [("suggested", "Suggested"), ("confirmed", "Confirmed")]
    TRACKER_CHOICES = [("myanimelist", "MyAnimeList"), ("anilist", "AniList")]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="tracker_links"
    )
    manga = models.ForeignKey(
        MediaItem,
        on_delete=models.CASCADE,
        related_name="tracker_links",
        limit_choices_to={"media_type": "Manga"},
    )
    tracker = models.CharField(max_length=20, choices=TRACKER_CHOICES)
    remote_id = models.CharField(max_length=50)
    remote_title = models.CharField(max_length=255, blank=True)
    # None = inconnue : on ne pousse pas tant qu'on n'a pas pu la lire.
    remote_progress = models.IntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="suggested"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "manga", "tracker")

    def __str__(self):
        return f"{self.user.username} - {self.manga.title} -> {self.tracker}:{self.remote_id}"
