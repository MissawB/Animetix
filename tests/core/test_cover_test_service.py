import pytest
import datetime
from unittest.mock import MagicMock
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
