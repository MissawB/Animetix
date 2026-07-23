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

    class Meta:
        model = FavoriteManga
        fields = [
            "id",
            "manga",
            "status",
            "last_read_chapter",
            "unread_chapters_count",
            "created_at",
            "updated_at",
        ]

    def get_unread_chapters_count(self, obj) -> int:
        if hasattr(obj, "unread_chapters_count_annotated"):
            return obj.unread_chapters_count_annotated
        return MangaChapter.objects.filter(
            manga=obj.manga, number__gt=obj.last_read_chapter
        ).count()
