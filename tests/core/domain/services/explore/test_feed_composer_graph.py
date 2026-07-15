import pytest
from animetix.models import FavoriteManga, MediaItem
from core.domain.services.explore.feed_composer import FeedComposer
from django.contrib.auth.models import User


class _CatalogFromDb:
    def get_catalog(self, media_type):
        db = [
            {
                "id": m.external_id,
                "title": m.title,
                "media_type": m.media_type,
                "image": m.image_url,
                "synopsis_fr": m.synopsis_fr,
                "year": m.release_year,
                "popularity": m.popularity,
                "rating": m.rating,
                "genres": (m.metadata or {}).get("genres", []),
            }
            for m in MediaItem.objects.filter(media_type=media_type)
        ]
        return {
            "db": db,
            "id_to_full_data": {str(i["id"]): i for i in db},
            "title_to_full_data": {i["title"]: i for i in db},
        }


class _SpyGraph:
    def __init__(self, neighbor_ids):
        self._neighbor_ids = neighbor_ids
        self.calls = []

    def get_neighborhood(self, item_id, media_type, depth=1):
        self.calls.append((item_id, media_type, depth))
        nodes = [
            {"id": 999, "properties": {"id": nid}, "labels": ["Media"]}
            for nid in self._neighbor_ids
        ]
        return {"nodes": nodes, "links": []}


@pytest.mark.django_db
def test_because_you_liked_builds_row_from_favorite_seed():
    user = User.objects.create_user(username="u", password="p")
    seed = MediaItem.objects.create(
        external_id="seed",
        media_type="Manga",
        title="Seed Manga",
    )
    FavoriteManga.objects.create(user=user, manga=seed, status="reading")
    neighbor_ids = []
    for i in range(1, 6):  # 5 voisins présents dans le catalogue Anime
        MediaItem.objects.create(
            external_id=f"n{i}",
            media_type="Anime",
            title=f"N{i}",
            popularity=i,
            rating=7.0,
            metadata={"genres": ["Action"]},
        )
        neighbor_ids.append(f"n{i}")
    graph = _SpyGraph(neighbor_ids)

    composer = FeedComposer(_CatalogFromDb(), graph)
    result = composer.compose(user=user, media_type="Anime")

    byl = next((r for r in result["rows"] if r["kind"] == "because_you_liked"), None)
    assert byl is not None
    assert byl["seed"] == {"id": "seed", "title": "Seed Manga"}
    assert "Seed Manga" in byl["title"]
    assert len(byl["items"]) == 5
    assert result["personalized"] is True
    # Bx : on a appelé le port graphe directement, jamais deduct_berrix
    assert graph.calls  # le port a bien été sollicité


@pytest.mark.django_db
def test_seed_with_too_few_neighbors_is_skipped():
    user = User.objects.create_user(username="u3", password="p")
    seed = MediaItem.objects.create(
        external_id="seed",
        media_type="Manga",
        title="Seed Manga",
    )
    FavoriteManga.objects.create(user=user, manga=seed, status="reading")
    MediaItem.objects.create(
        external_id="n1", media_type="Anime", title="N1", popularity=1, rating=7.0
    )
    graph = _SpyGraph(["n1"])  # 1 seul voisin < MIN_ROW_ITEMS

    composer = FeedComposer(_CatalogFromDb(), graph)
    result = composer.compose(user=user, media_type="Anime")

    assert all(r["kind"] != "because_you_liked" for r in result["rows"])
