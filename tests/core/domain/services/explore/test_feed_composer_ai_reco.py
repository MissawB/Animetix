import pytest
from animetix.models import MediaItem, UserRecommendation
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


class _NoGraph:
    def get_neighborhood(self, item_id, media_type, depth=1):
        return {"nodes": [], "links": []}


@pytest.mark.django_db
def test_ai_reco_row_present_and_personalized():
    user = User.objects.create_user(username="u", password="p")
    for i in range(1, 8):
        MediaItem.objects.create(
            external_id=str(i),
            media_type="Anime",
            title=f"A{i}",
            popularity=10 - i,
            rating=8.0,
            metadata={"genres": ["Action"]},
        )
    reco = MediaItem.objects.get(external_id="3")
    UserRecommendation.objects.create(user=user, media_item=reco, score=0.9, rank=1)

    composer = FeedComposer(_CatalogFromDb(), _NoGraph())
    result = composer.compose(user=user, media_type="Anime")

    ai = next((r for r in result["rows"] if r["kind"] == "ai_reco"), None)
    assert ai is not None
    assert result["rows"][0]["kind"] == "ai_reco"  # en tête
    assert ai["items"][0]["id"] == "3"
    assert result["personalized"] is True


@pytest.mark.django_db
def test_ai_reco_absent_without_recommendations():
    user = User.objects.create_user(username="u2", password="p")
    for i in range(1, 8):
        MediaItem.objects.create(
            external_id=str(i),
            media_type="Anime",
            title=f"A{i}",
            popularity=10 - i,
            rating=8.0,
            metadata={"genres": ["Action"]},
        )
    composer = FeedComposer(_CatalogFromDb(), _NoGraph())
    result = composer.compose(user=user, media_type="Anime")

    assert all(r["kind"] != "ai_reco" for r in result["rows"])
    assert result["personalized"] is False
