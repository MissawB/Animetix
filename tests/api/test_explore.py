import pytest
from animetix.models import MediaItem, UserRecommendation
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


def _reset_catalog_cache():
    import sys

    cache.clear()
    mod = sys.modules.get("animetix.containers")
    if mod is not None:
        try:
            mod.container.core.catalog_service()._cached_catalogs.clear()
        except Exception:
            pass


@pytest.mark.django_db
def test_explore_returns_feed_shape(api_client):
    for i in range(1, 8):
        MediaItem.objects.create(
            external_id=str(i),
            media_type="Anime",
            title=f"A{i}",
            popularity=10 - i,
            rating=8.0,
            metadata={"genres": ["Action"]},
        )
    _reset_catalog_cache()

    url = reverse("api_explore")
    response = api_client.get(url, {"media_type": "Anime"})

    assert response.status_code == status.HTTP_200_OK
    assert "rows" in response.data
    assert "personalized" in response.data
    assert response.data["personalized"] is False  # anonyme → cold-start
    kinds = {r["kind"] for r in response.data["rows"]}
    assert kinds & {"top_rated", "new"}


@pytest.mark.django_db
def test_explore_personalized_with_recommendation(api_client):
    user = User.objects.create_user(username="testuser", password="password")
    api_client.force_authenticate(user=user)
    media = MediaItem.objects.create(
        external_id="test-1",
        title="Test Media",
        media_type="Anime",
        popularity=5,
        rating=8.0,
        metadata={"genres": ["Action"]},
    )
    for i in range(2, 7):
        MediaItem.objects.create(
            external_id=str(i),
            media_type="Anime",
            title=f"A{i}",
            popularity=i,
            rating=7.0,
            metadata={"genres": ["Action"]},
        )
    UserRecommendation.objects.create(user=user, media_item=media, score=0.9, rank=1)
    _reset_catalog_cache()

    url = reverse("api_explore")
    response = api_client.get(url, {"media_type": "Anime"})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["personalized"] is True
    assert response.data["rows"][0]["kind"] == "ai_reco"
    assert response.data["rows"][0]["items"][0]["id"] == "test-1"
