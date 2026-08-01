from django.db.models import Q
from rest_framework import serializers

from ..models import FavoriteManga, MangaChapter, MangaPage
from .catalog import MediaItemSerializer


class MangaPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MangaPage
        fields = ["id", "number", "image_url", "metadata"]


class MangaChapterSerializer(serializers.ModelSerializer):
    pages = MangaPageSerializer(many=True, read_only=True)

    class Meta:
        model = MangaChapter
        fields = [
            "id",
            "manga",
            "number",
            "title",
            "external_id",
            "pages",
            "created_at",
            "updated_at",
        ]


class FavoriteMangaSerializer(serializers.ModelSerializer):
    manga = MediaItemSerializer(read_only=True)
    unread_chapters_count = serializers.SerializerMethodField()
    read_count = serializers.SerializerMethodField()
    total_chapters = serializers.SerializerMethodField()
    has_started = serializers.SerializerMethodField()

    class Meta:
        model = FavoriteManga
        fields = [
            "id",
            "manga",
            "status",
            "last_read_chapter",
            "unread_chapters_count",
            "read_count",
            "total_chapters",
            "has_started",
            "created_at",
            "updated_at",
        ]

    def get_unread_chapters_count(self, obj) -> int:
        if hasattr(obj, "unread_chapters_count_annotated"):
            return obj.unread_chapters_count_annotated
        return MangaChapter.objects.filter(
            manga=obj.manga, number__gt=obj.last_read_chapter
        ).count()

    def get_read_count(self, obj) -> int:
        if hasattr(obj, "read_count_annotated"):
            return obj.read_count_annotated
        return MangaChapter.objects.filter(
            manga=obj.manga, progress__user=obj.user, progress__is_read=True
        ).count()

    def get_total_chapters(self, obj) -> int:
        if hasattr(obj, "total_chapters_annotated"):
            return obj.total_chapters_annotated
        return MangaChapter.objects.filter(manga=obj.manga).count()

    def get_has_started(self, obj) -> bool:
        """Au moins un chapitre entamé — pas seulement terminé.

        `read_count` ne suffit pas à décider d'un « Reprendre » : quelqu'un au
        milieu du chapitre 1 a `read_count == 0` alors que la fiche œuvre et la
        popup lui proposent bien de reprendre.
        """
        if hasattr(obj, "has_started_annotated"):
            return bool(obj.has_started_annotated)
        return MangaChapter.objects.filter(
            Q(progress__is_read=True) | Q(progress__last_page_read__gt=0),
            manga=obj.manga,
            progress__user=obj.user,
        ).exists()
