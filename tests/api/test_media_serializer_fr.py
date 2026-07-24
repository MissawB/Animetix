import pytest
from animetix.models import MediaItem
from animetix.serializers import MediaItemSerializer


@pytest.mark.django_db
def test_serializer_prefers_synopsis_fr_when_present():
    item = MediaItem.objects.create(
        external_id="1",
        media_type="Anime",
        title="Show",
        description="English synopsis.",
        synopsis_fr="Synopsis en français.",
    )
    assert MediaItemSerializer(item).data["description"] == "Synopsis en français."


@pytest.mark.django_db
def test_serializer_falls_back_to_english_without_fr():
    item = MediaItem.objects.create(
        external_id="2",
        media_type="Anime",
        title="Show2",
        description="English synopsis.",
    )
    assert MediaItemSerializer(item).data["description"] == "English synopsis."
