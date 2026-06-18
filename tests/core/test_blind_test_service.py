import datetime
from unittest.mock import MagicMock

import pytest
from core.domain.services.blind_test_service import BlindTestDomainService


@pytest.fixture
def mock_repository():
    repo = MagicMock()
    repo.load_themes.return_value = {
        "1": {
            "title": "Naruto",
            "themes": [
                {
                    "type": "OP",
                    "song_title": "GO!!!",
                    "artists": "FLOW",
                    "entries": [{"videos": [{"link": "http://video"}]}],
                }
            ],
        }
    }
    return repo


@pytest.fixture
def blind_test_service(mock_repository):
    return BlindTestDomainService(repository=mock_repository)


def test_get_random_theme(blind_test_service):
    theme = blind_test_service.get_random_theme()
    assert theme is not None
    assert theme["anime_title"] == "Naruto"
    assert theme["video_url"] == "http://video"


def test_get_random_theme_specific_type(blind_test_service):
    theme = blind_test_service.get_random_theme(theme_type="OP")
    assert theme is not None

    theme_ed = blind_test_service.get_random_theme(theme_type="ED")
    assert theme_ed is None  # No ED in mock data


def test_get_daily_theme(blind_test_service):
    date_obj = datetime.date(2023, 1, 1)
    theme = blind_test_service.get_daily_theme(date_obj)
    assert theme is not None
    assert theme["anime_title"] == "Naruto"


def test_empty_catalog(blind_test_service, mock_repository):
    mock_repository.load_themes.return_value = {}
    blind_test_service._themes = None  # reset cache
    assert blind_test_service.get_random_theme() is None
