import pytest
from animetix.models import MediaItem
from django.urls import reverse
from rest_framework.test import APIClient


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
    # The CatalogService is a DI singleton that caches catalogs in-memory for the
    # whole session; clear it (in both import namespaces) plus the Django cache so
    # the explore view reflects the rows just created instead of a stale catalog.
    import sys

    from django.core.cache import cache

    cache.clear()
    for mod_name in ("animetix.containers", "animetix.containers"):
        mod = sys.modules.get(mod_name)
        if mod is not None:
            try:
                mod.container.core.catalog_service()._cached_catalogs.clear()
            except Exception:
                pass
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
