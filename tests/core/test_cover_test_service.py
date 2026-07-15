import datetime
import random
from unittest.mock import MagicMock

import pytest
from core.domain.services.cover_test_service import CoverTestDomainService


@pytest.fixture
def mock_repository():
    repo = MagicMock()
    repo.load_covers.return_value = {
        "1": {
            "title": "One Piece",
            "covers": {
                "ja": [{"url": "http://cover_ja", "volume": "1"}],
                "fr": [{"url": "http://cover_fr", "volume": "2"}],
            },
        }
    }

    def get_metadata_side_effect():
        catalog = repo.load_covers.return_value or {}
        metadata = []
        for mid, info in catalog.items():
            metadata.append(
                {
                    "id": str(mid),
                    "title": info.get("title", ""),
                    "title_english": info.get("title_english"),
                    "title_native": info.get("title_native"),
                    "synonyms": info.get("synonyms", []),
                    "author": info.get("author"),
                    "has_ja": bool(info.get("covers", {}).get("ja")),
                    "has_fr": bool(info.get("covers", {}).get("fr")),
                }
            )
        return metadata

    repo.get_manga_covers_metadata.side_effect = get_metadata_side_effect

    def get_by_id_side_effect(manga_id):
        catalog = repo.load_covers.return_value or {}
        mid = str(manga_id)
        if mid not in catalog:
            return None
        info = catalog[mid]
        return {
            "title": info.get("title", ""),
            "mangadex_id": info.get("mangadex_id"),
            "covers": info.get("covers", {}),
            "title_english": info.get("title_english"),
            "title_native": info.get("title_native"),
            "synonyms": info.get("synonyms", []),
            "author": info.get("author"),
        }

    repo.get_manga_cover_by_id.side_effect = get_by_id_side_effect

    def get_by_title_side_effect(title):
        catalog = repo.load_covers.return_value or {}
        for mid, info in catalog.items():
            if info.get("title") == title:
                return get_by_id_side_effect(mid)
        return None

    repo.get_manga_cover_by_title.side_effect = get_by_title_side_effect

    return repo


@pytest.fixture
def cover_test_service(mock_repository):
    return CoverTestDomainService(repository=mock_repository)


def test_get_random_cover(cover_test_service):
    cover = cover_test_service.get_random_cover()
    assert cover is not None
    assert cover["manga_title"] == "One Piece"
    assert cover["cover_url"] in ["http://cover_ja", "http://cover_fr"]


def test_get_random_cover_locale(cover_test_service):
    cover = cover_test_service.get_random_cover(locale="ja")
    assert cover is not None
    assert cover["locale"] == "ja"
    assert cover["cover_url"] == "http://cover_ja"


def test_get_daily_cover(cover_test_service):
    date_obj = datetime.date(2023, 1, 1)
    cover = cover_test_service.get_daily_cover(date_obj)
    assert cover is not None


def test_empty_catalog(cover_test_service, mock_repository):
    mock_repository.load_covers.return_value = {}
    cover_test_service._covers = None  # reset cache
    assert cover_test_service.get_random_cover() is None


def test_random_cover_draws_from_every_volume(mock_repository):
    """Le tirage doit balayer tous les tomes, pas se figer sur le tome 1."""
    mock_repository.load_covers.return_value = {
        "1": {
            "title": "Berserk",
            "covers": {
                "ja": [{"url": f"http://v{v}", "volume": str(v)} for v in range(1, 42)],
                "fr": [],
            },
        }
    }
    service = CoverTestDomainService(repository=mock_repository)

    seen = {service.get_random_cover(locale="ja")["volume"] for _ in range(300)}

    assert len(seen) > 1, "un seul volume tiré sur 300 essais => biais tome 1"
    assert seen - {str(v) for v in range(1, 42)} == set()


def test_random_cover_picks_manga_uniformly_not_per_volume(mock_repository):
    """Une série de 100 tomes ne doit pas sortir 100x plus qu'un one-shot."""
    mock_repository.load_covers.return_value = {
        "long": {
            "title": "Long Series",
            "covers": {
                "ja": [{"url": f"http://l{v}", "volume": str(v)} for v in range(100)],
                "fr": [],
            },
        },
        "short": {
            "title": "One Shot",
            "covers": {"ja": [{"url": "http://s1", "volume": "1"}], "fr": []},
        },
    }
    service = CoverTestDomainService(repository=mock_repository)

    draws = [service.get_random_cover(locale="ja")["manga_id"] for _ in range(400)]

    # Uniforme par manga => ~50/50. Un tirage à plat sur les volumes donnerait
    # ~99 % de "long" et ce seuil sauterait.
    assert draws.count("short") > 100


def test_ignores_mangas_without_cover_in_requested_locale(mock_repository):
    mock_repository.load_covers.return_value = {
        "1": {
            "title": "JA only",
            "covers": {"ja": [{"url": "http://ja", "volume": "1"}], "fr": []},
        },
        "2": {
            "title": "FR only",
            "covers": {"ja": [], "fr": [{"url": "http://fr", "volume": "1"}]},
        },
    }
    service = CoverTestDomainService(repository=mock_repository)

    for _ in range(20):
        cover = service.get_random_cover(locale="fr")
        assert cover["manga_id"] == "2"


def test_no_cover_in_requested_locale_returns_none(mock_repository):
    mock_repository.load_covers.return_value = {
        "1": {
            "title": "JA only",
            "covers": {"ja": [{"url": "http://ja", "volume": "1"}], "fr": []},
        }
    }
    service = CoverTestDomainService(repository=mock_repository)

    assert service.get_random_cover(locale="fr") is None


def test_daily_cover_is_stable_for_a_given_day(mock_repository):
    mock_repository.load_covers.return_value = {
        str(i): {
            "title": f"M{i}",
            "covers": {
                "ja": [{"url": f"http://{i}-{v}", "volume": str(v)} for v in range(5)],
                "fr": [],
            },
        }
        for i in range(30)
    }
    service = CoverTestDomainService(repository=mock_repository)
    day = datetime.date(2026, 7, 12)

    picks = {service.get_daily_cover(day)["cover_url"] for _ in range(10)}

    assert len(picks) == 1  # même jour => même cover, volume compris
    assert service.get_daily_cover(datetime.date(2026, 7, 13)) is not None


def test_daily_cover_does_not_reseed_the_global_rng(cover_test_service):
    """Le daily utilisait random.seed() global : sous daphne, deux requêtes
    concurrentes se marchaient dessus."""
    random.seed(1234)
    expected = [random.random() for _ in range(3)]

    random.seed(1234)
    cover_test_service.get_daily_cover(datetime.date(2026, 7, 12))

    assert [random.random() for _ in range(3)] == expected
