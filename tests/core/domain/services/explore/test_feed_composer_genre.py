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


class _NoGraph:
    def get_neighborhood(self, item_id, media_type, depth=1):
        return {"nodes": [], "links": []}


@pytest.mark.django_db
def test_genre_affinity_row_from_favorite_genres():
    user = User.objects.create_user(username="u", password="p")
    fav = MediaItem.objects.create(
        external_id="fav",
        media_type="Manga",
        title="Fav",
        metadata={"genres": ["Romance"]},
    )
    FavoriteManga.objects.create(user=user, manga=fav, status="reading")
    for i in range(1, 6):
        MediaItem.objects.create(
            external_id=f"r{i}",
            media_type="Anime",
            title=f"R{i}",
            popularity=i,
            rating=7.0,
            metadata={"genres": ["Romance"]},
        )
    composer = FeedComposer(_CatalogFromDb(), _NoGraph())
    result = composer.compose(user=user, media_type="Anime")

    genre = next((r for r in result["rows"] if r["kind"] == "genre_affinity"), None)
    assert genre is not None
    assert "Romance" in genre["title"]
    assert len(genre["items"]) >= 4
