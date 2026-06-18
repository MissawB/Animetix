import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from animetix.models import MediaItem


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def media_items(db):
    for i in range(1, 10):
        MediaItem.objects.create(
            external_id=str(i),
            media_type="Anime",
            title=f"Anime {i}",
            popularity=100.0 - i,
            metadata={"genres": ["Action"]},
        )
    return MediaItem.objects.all()


@pytest.mark.django_db
def test_media_explore_view(api_client, media_items):
    url = reverse("api_explore")
    response = api_client.get(url, {"media_type": "Anime"})
    assert response.status_code == 200
    assert len(response.data["trending"]) >= 1
    # On vérifie qu'une catégorie "Action" a été créée
    action_cat = next(
        (c for c in response.data["categories"] if c["name"] == "Action"), None
    )
    assert action_cat is not None
    assert len(action_cat["items"]) >= 5
