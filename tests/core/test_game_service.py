import pytest
from unittest.mock import MagicMock
from core.domain.services.game_service import GameService


@pytest.fixture
def mock_repository():
    return MagicMock()


@pytest.fixture
def mock_catalog_service():
    return MagicMock()


@pytest.fixture
def mock_similarity_service():
    return MagicMock()


@pytest.fixture
def mock_undercover_service():
    return MagicMock()


@pytest.fixture
def game_service(
    mock_repository,
    mock_catalog_service,
    mock_similarity_service,
    mock_undercover_service,
):
    return GameService(
        repository=mock_repository,
        catalog_service=mock_catalog_service,
        similarity_service=mock_similarity_service,
        undercover_service=mock_undercover_service,
    )


def test_get_catalog_delegation(game_service, mock_catalog_service):
    mock_catalog_service.get_catalog.return_value = {"db": []}
    catalog = game_service.get_catalog("Anime")
    assert catalog == {"db": []}
    mock_catalog_service.get_catalog.assert_called_once_with("Anime")


def test_calculate_raw_similarity_delegation(game_service, mock_similarity_service):
    mock_similarity_service.calculate_raw_similarity.return_value = 0.9
    res = game_service.calculate_raw_similarity("Anime", "A", "B", {})
    assert res == 0.9
    mock_similarity_service.calculate_raw_similarity.assert_called_once()


def test_select_secret(game_service, mock_catalog_service):
    item = {"id": 1, "title": "Naruto"}
    catalog = {"lookup": [item], "title_to_full_data": {"Naruto": item}}
    mock_catalog_service.get_catalog.return_value = catalog

    res = game_service.select_secret("Anime", "Normal", {"Anime": {"Normal": 100}})
    assert res == "Naruto"


def test_start_undercover_game_delegation(game_service, mock_undercover_service):
    mock_undercover_service.start_game.return_value = {"ok": True}
    res = game_service.start_undercover_game("Anime", "Easy", ["P1"], {})
    assert res == {"ok": True}
    mock_undercover_service.start_game.assert_called_once()
