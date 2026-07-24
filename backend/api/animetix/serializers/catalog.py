from core.utils.security import sanitize_html_content
from rest_framework import serializers


class MediaItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    title_english = serializers.CharField(required=False, allow_null=True)
    title_native = serializers.CharField(required=False, allow_null=True)
    image = serializers.URLField(required=False, allow_null=True)
    type = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    year = serializers.IntegerField(required=False, allow_null=True)
    popularity = serializers.IntegerField(required=False, allow_null=True)
    rating = serializers.FloatField(required=False, allow_null=True)
    genres = serializers.ListField(child=serializers.CharField(), required=False)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    micro_tags = serializers.ListField(child=serializers.CharField(), required=False)
    description = serializers.CharField(required=False, allow_null=True)

    studios = serializers.ListField(child=serializers.CharField(), required=False)
    author = serializers.CharField(required=False, allow_null=True)
    related_items = serializers.ListField(child=serializers.DictField(), required=False)
    streaming_platforms = serializers.ListField(
        child=serializers.DictField(), required=False
    )

    @staticmethod
    def _media_type(obj):
        if isinstance(obj, dict):
            return obj.get("media_type") or obj.get("type")
        return getattr(obj, "media_type", None)

    def get_type(self, obj):
        return self._media_type(obj)

    def get_image_url(self, obj):
        if isinstance(obj, dict):
            return obj.get("image") or obj.get("image_url")
        return getattr(obj, "image_url", None)

    def to_representation(self, instance):
        from django.db import models

        if isinstance(instance, models.Model):
            manga_metadata = getattr(instance, "metadata", {}) or {}
            mapped_instance = {
                "id": getattr(instance, "external_id", None),
                "title": getattr(instance, "title", ""),
                "title_english": getattr(instance, "title_english", None),
                "title_native": getattr(instance, "title_native", None),
                "image": getattr(instance, "image_url", None),
                "media_type": getattr(instance, "media_type", None),
                "year": getattr(instance, "release_year", None),
                "popularity": int(getattr(instance, "popularity", 0) or 0),
                "rating": getattr(instance, "rating", None),
                "genres": manga_metadata.get("genres", []),
                "tags": manga_metadata.get("tags", []),
                "micro_tags": manga_metadata.get("micro_tags", []),
                "description": getattr(instance, "synopsis_fr", None)
                or getattr(instance, "description", "")
                or "",
                "studios": manga_metadata.get("studios", []),
                "author": manga_metadata.get("author", None),
                "related_items": manga_metadata.get("related_items", []),
                "streaming_platforms": manga_metadata.get("streaming_platforms") or [],
            }
            instance = mapped_instance

        if isinstance(instance, dict) and isinstance(instance.get("popularity"), dict):
            instance = {
                **instance,
                "popularity": int(instance["popularity"].get("favourites") or 0),
            }

        if isinstance(instance, dict) and "streaming_platforms" not in instance:
            instance = {**instance, "streaming_platforms": []}

        ret = super().to_representation(instance)
        if ret.get("description"):
            ret["description"] = sanitize_html_content(ret["description"])

        for key in ["tags", "micro_tags", "genres"]:
            if ret.get(key):
                ret[key] = [sanitize_html_content(t) for t in ret[key]]

        return ret
