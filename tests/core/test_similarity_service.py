import pytest
from unittest.mock import MagicMock
from core.domain.services.similarity_service import SimilarityService

@pytest.fixture
def mock_repository():
    return MagicMock()

@pytest.fixture
def similarity_service(mock_repository):
    return SimilarityService(repository=mock_repository)

def test_check_title_match(similarity_service):
    item = {
        'title': 'Attack on Titan',
        'title_native': 'Shingeki no Kyojin',
        'alternative_titles': ['AOT'],
        'metadata': {'synonyms': ['Attack']}
    }
    
    assert similarity_service.check_title_match("Attack on Titan", item) is True
    assert similarity_service.check_title_match("Attack", item) is True
    assert similarity_service.check_title_match("snk", item) is True 
    assert similarity_service.check_title_match("Naruto", item) is False

def test_calculate_raw_similarity_character(similarity_service, mock_repository):
    data = {
        'title_to_full_data': {
            'Luffy': {'id': 0, 'title': 'Luffy', 'metadata': {'affiliations': ['Pirates']}},
            'Zoro': {'id': 1, 'title': 'Zoro', 'metadata': {'affiliations': ['Pirates']}}
        }
    }
    mock_repository.calculate_similarity.return_value = 0.5
    res = similarity_service.calculate_raw_similarity('Character', 'Luffy', 'Zoro', data)
    # 0.7 * 0.5 + 0.3 * 1.0 = 0.35 + 0.3 = 0.65
    assert res == pytest.approx(0.65)

def test_calculate_similarity(similarity_service, mock_repository):
    mock_repository.calculate_similarity.return_value = 0.8
    assert similarity_service.calculate_similarity('Anime', '1', '2') == 0.8
