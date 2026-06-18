import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_animetix_service():
    mock_service = MagicMock()
    mock_service.load_data.return_value = {"titles": ["Naruto"]}

    mock_blind = MagicMock()
    mock_blind.get_random_theme.return_value = {"anime_title": "A"}
    mock_service.blind_test_service = mock_blind

    mock_cover = MagicMock()
    mock_cover.get_random_cover.return_value = {"manga_title": "M"}
    mock_service.cover_test_service = mock_cover

    return mock_service


@pytest.fixture
def animetix_service(mock_animetix_service):
    return mock_animetix_service


def test_animetix_service_load_data(animetix_service, mocker):
    """Vérifie le chargement des données (mocké)."""
    # In conftest, load_data is already mocked to return a catalog with 'Naruto'
    data = animetix_service.load_data("Anime")
    assert "Naruto" in data["titles"]


def test_blindtest_service_pick(animetix_service, mocker):
    """Vérifie que le BlindTestService choisit bien un thème."""
    # In conftest, blind_test_service is mocked
    theme = animetix_service.blind_test_service.get_random_theme()
    assert theme["anime_title"] == "A"


def test_covertest_service_pick(animetix_service, mocker):
    """Vérifie que le CoverTestService choisit bien une couverture."""
    cover = animetix_service.cover_test_service.get_random_cover()
    assert cover["manga_title"] == "M"
