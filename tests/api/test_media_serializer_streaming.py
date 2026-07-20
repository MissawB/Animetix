import pytest
from animetix.models import MediaItem
from animetix.serializers import MediaItemSerializer


@pytest.mark.django_db
def test_serializer_exposes_streaming_platforms():
    item = MediaItem.objects.create(
        external_id="1",
        media_type="Anime",
        title="Show",
        metadata={
            "streaming_platforms": [
                {
                    "platform": "Crunchyroll",
                    "has_vf": True,
                    "has_vostfr": True,
                    "status": "Abonnement",
                }
            ]
        },
    )
    data = MediaItemSerializer(item).data
    assert data["streaming_platforms"][0]["platform"] == "Crunchyroll"


@pytest.mark.django_db
def test_serializer_streaming_platforms_defaults_to_empty():
    item = MediaItem.objects.create(
        external_id="2", media_type="Anime", title="Show2", metadata={}
    )
    data = MediaItemSerializer(item).data
    assert data["streaming_platforms"] == []
