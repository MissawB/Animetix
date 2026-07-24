from django.contrib.auth.models import User
from django.db import models


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
