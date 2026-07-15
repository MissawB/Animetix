import pytest
from core.domain.services.explore.feed_composer import FeedComposer


class _FakeCatalog:
    """catalog_service qui renvoie un catalogue fixe, indexé comme le vrai."""

    def __init__(self, items):
        self._items = items

    def get_catalog(self, media_type):
        db = [i for i in self._items if i["media_type"] == media_type]
        return {
            "db": db,
            "id_to_full_data": {str(i["id"]): i for i in db},
            "title_to_full_data": {i["title"]: i for i in db},
        }


class _NoGraph:
    def get_neighborhood(self, item_id, media_type, depth=1):
        return {"nodes": [], "links": []}


def _anime(n, **kw):
    base = {
        "id": str(n),
        "title": f"Anime {n}",
        "media_type": "Anime",
        "image": f"img{n}",
        "synopsis_fr": f"syn {n}",
        "year": 2000 + n,
        "popularity": 100 - n,
        "rating": 9.0 - n * 0.1,
        "genres": ["Action"],
    }
    base.update(kw)
    return base


@pytest.fixture
def catalog_items():
    return [_anime(i) for i in range(1, 13)]


def test_cold_start_returns_top_rated_and_new_and_not_personalized(catalog_items):
    composer = FeedComposer(_FakeCatalog(catalog_items), _NoGraph())

    result = composer.compose(user=None, media_type="Anime")

    kinds = [r["kind"] for r in result["rows"]]
    assert "top_rated" in kinds
    assert "new" in kinds
    assert result["personalized"] is False
    # top_rated trié par note décroissante
    top = next(r for r in result["rows"] if r["kind"] == "top_rated")
    ratings = [it["rating"] for it in top["items"]]
    assert ratings == sorted(ratings, reverse=True)
    # new trié par année décroissante
    new = next(r for r in result["rows"] if r["kind"] == "new")
    years = [it["year"] for it in new["items"]]
    assert years == sorted(years, reverse=True)
    # les items sont sérialisés avec les clés attendues
    assert set(top["items"][0].keys()) >= {
        "id",
        "title",
        "media_type",
        "image",
        "synopsis_fr",
        "year",
        "popularity",
        "rating",
        "genres",
    }
