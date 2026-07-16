import pytest
from animetix.models import MediaItem
from django.core.cache import cache
from django.urls import reverse


@pytest.fixture
def media_items(db):
    for i in range(1, 10):
        MediaItem.objects.create(
            external_id=str(i),
            media_type="Anime",
            title=f"Anime {i}",
            popularity=100.0 - i,
            rating=9.0 - i * 0.1,
            metadata={"genres": ["Action"]},
        )
    import sys

    cache.clear()
    mod = sys.modules.get("animetix.containers")
    if mod is not None:
        try:
            mod.container.core.catalog_service()._cached_catalogs.clear()
        except Exception:
            pass
    return MediaItem.objects.all()


@pytest.mark.django_db
def test_media_explore_view_returns_rows(api_client, media_items):
    url = reverse("api_explore")
    response = api_client.get(url, {"media_type": "Anime"})
    assert response.status_code == 200
    assert len(response.data["rows"]) >= 1
    top = next(r for r in response.data["rows"] if r["kind"] == "top_rated")
    assert len(top["items"]) >= 1
