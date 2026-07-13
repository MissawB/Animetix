from unittest.mock import MagicMock

import pytest
from core.domain.services.similarity_service import SimilarityService


@pytest.fixture
def mock_repository():
    return MagicMock()


@pytest.fixture
def similarity_service(mock_repository):
    return SimilarityService(repository=mock_repository)


def test_check_title_match(similarity_service):
    item = {
        "title": "Attack on Titan",
        "title_native": "Shingeki no Kyojin",
        "alternative_titles": ["AOT"],
        "metadata": {"synonyms": ["Attack"]},
    }

    assert similarity_service.check_title_match("Attack on Titan", item) is True
    assert similarity_service.check_title_match("Attack", item) is True
    assert similarity_service.check_title_match("snk", item) is True
    assert similarity_service.check_title_match("Naruto", item) is False


def test_calculate_raw_similarity_character(similarity_service, mock_repository):
    data = {
        "title_to_full_data": {
            "Luffy": {
                "id": 0,
                "title": "Luffy",
                "metadata": {"affiliations": ["Pirates"]},
            },
            "Zoro": {
                "id": 1,
                "title": "Zoro",
                "metadata": {"affiliations": ["Pirates"]},
            },
        }
    }
    mock_repository.calculate_similarity.return_value = 0.5
    res = similarity_service.calculate_raw_similarity(
        "Character", "Luffy", "Zoro", data
    )
    # Similarité vectorielle brute, sans mélange avec un terme graphe.
    assert res == pytest.approx(0.5)


def test_calculate_similarity(similarity_service, mock_repository):
    mock_repository.calculate_similarity.return_value = 0.8
    assert similarity_service.calculate_similarity("Anime", "1", "2") == 0.8


def test_the_dead_neo4j_path_is_gone():
    """Ce terme valait 0.3 du score et 0.0 en réalité : le conteneur n'a jamais injecté
    neo4j_manager. Une pondération structurellement nulle est un mensonge."""
    import inspect

    from core.domain.services import similarity_service as module

    source = inspect.getsource(module)
    assert "neo4j" not in source.lower()
    assert "0.3" not in source  # plus de mélange 70/30


def test_similarity_is_the_vector_score_alone(monkeypatch):
    from unittest.mock import MagicMock

    from core.domain.services.similarity_service import SimilarityService

    repository = MagicMock()
    repository.calculate_similarity.return_value = 0.42
    service = SimilarityService(repository=repository)
    catalog = {"title_to_full_data": {"A": {"id": "1"}, "B": {"id": "2"}}}

    assert service.calculate_raw_similarity("Anime", "A", "B", catalog) == 0.42
