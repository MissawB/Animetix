import pytest
from adapters.persistence.django_manga_progress_repository_adapter import (
    DjangoMangaProgressRepositoryAdapter,
)
from animetix.models import (
    FavoriteManga,
    MangaChapter,
    MangaPage,
    MangaReadingProgress,
    MediaItem,
)
from django.contrib.auth.models import User


@pytest.fixture
def fixtures(db):
    user = User.objects.create_user(username="reader", password="pw")
    manga = MediaItem.objects.create(
        external_id="suwayomi:1:809", media_type="Manga", title="OPM"
    )
    c1 = MangaChapter.objects.create(manga=manga, number=1.0, external_id="1")
    c2 = MangaChapter.objects.create(manga=manga, number=164.2, external_id="2")
    for i in range(1, 4):
        MangaPage.objects.create(chapter=c1, number=i, image_url=f"http://h/{i}.jpg")
    return user, manga, c1, c2


def test_list_chapters_with_progress_joins_pages_and_progress(fixtures):
    user, manga, c1, _c2 = fixtures
    MangaReadingProgress.objects.create(
        user=user, chapter=c1, last_page_read=2, is_read=True
    )

    repo = DjangoMangaProgressRepositoryAdapter()
    rows = repo.list_chapters_with_progress(user, "suwayomi:1:809")

    assert [r["number"] for r in rows] == [1.0, 164.2]
    assert rows[0]["is_read"] is True
    assert rows[0]["last_page_read"] == 2
    assert rows[0]["page_count"] == 3
    assert rows[0]["external_id"] == "1"
    # Chapitre jamais ouvert : valeurs neutres, pas de page connue.
    assert rows[1]["is_read"] is False
    assert rows[1]["last_page_read"] == 0
    assert rows[1]["page_count"] == 0
    assert rows[1]["updated_at"] is None


def test_list_chapters_is_scoped_to_the_user(fixtures):
    user, _manga, c1, _c2 = fixtures
    other = User.objects.create_user(username="someone_else", password="pw")
    MangaReadingProgress.objects.create(
        user=other, chapter=c1, last_page_read=99, is_read=True
    )

    repo = DjangoMangaProgressRepositoryAdapter()
    rows = repo.list_chapters_with_progress(user, "suwayomi:1:809")

    assert rows[0]["is_read"] is False
    assert rows[0]["last_page_read"] == 0


def test_upsert_progress_creates_then_updates(fixtures):
    user, _manga, c1, _c2 = fixtures
    repo = DjangoMangaProgressRepositoryAdapter()

    repo.upsert_progress(user, c1, last_page_read=3, is_read=False)
    repo.upsert_progress(user, c1, last_page_read=7, is_read=True)

    row = MangaReadingProgress.objects.get(user=user, chapter=c1)
    assert (row.last_page_read, row.is_read) == (7, True)
    assert MangaReadingProgress.objects.count() == 1


def test_bulk_set_read_and_favorite_update(fixtures):
    user, manga, c1, c2 = fixtures
    repo = DjangoMangaProgressRepositoryAdapter()

    assert repo.bulk_set_read(user, [c1, c2], is_read=True) == 2
    assert MangaReadingProgress.objects.filter(user=user, is_read=True).count() == 2

    repo.set_favorite_last_read(user, manga, 164.2)
    assert FavoriteManga.objects.get(user=user, manga=manga).last_read_chapter == 164.2


def test_bulk_set_read_preserves_started_progress_with_constant_queries(
    fixtures, django_assert_num_queries
):
    """Un chapitre déjà entamé garde sa page ; un chapitre vierge repart à 0.

    Le nombre de requêtes doit rester constant quel que soit le nombre de
    chapitres traités (pas de N+1) : 1 lecture groupée + 1 bulk_update
    (chapitre déjà suivi) + 1 bulk_create (chapitre encore inconnu).
    """
    user, _manga, c1, c2 = fixtures
    MangaReadingProgress.objects.create(
        user=user, chapter=c1, last_page_read=2, is_read=False
    )
    repo = DjangoMangaProgressRepositoryAdapter()

    with django_assert_num_queries(3):
        processed = repo.bulk_set_read(user, [c1, c2], is_read=True)

    assert processed == 2
    c1_row = MangaReadingProgress.objects.get(user=user, chapter=c1)
    c2_row = MangaReadingProgress.objects.get(user=user, chapter=c2)
    # c1 était déjà à la page 2 : is_read=True conserve cette position.
    assert (c1_row.last_page_read, c1_row.is_read) == (2, True)
    # c2 n'avait jamais été ouvert : pas de page connue à conserver.
    assert (c2_row.last_page_read, c2_row.is_read) == (0, True)


def test_set_favorite_last_read_never_decreases(fixtures):
    user, manga, _c1, _c2 = fixtures
    repo = DjangoMangaProgressRepositoryAdapter()

    repo.set_favorite_last_read(user, manga, 164.2)
    repo.set_favorite_last_read(user, manga, 1.0)

    assert FavoriteManga.objects.get(user=user, manga=manga).last_read_chapter == 164.2
