import pytest
from unittest.mock import MagicMock
from core.domain.services.undercover_service import UndercoverService

@pytest.fixture
def mock_catalog_service():
    return MagicMock()

@pytest.fixture
def mock_similarity_service():
    return MagicMock()

@pytest.fixture
def undercover_service(mock_catalog_service, mock_similarity_service):
    return UndercoverService(catalog_service=mock_catalog_service, similarity_service=mock_similarity_service)

def test_start_game_success(undercover_service, mock_catalog_service, mock_similarity_service):
    item1 = {'id': 1, 'title': 'Naruto', 'image': 'naruto.jpg'}
    item2 = {'id': 2, 'title': 'Sasuke', 'image': 'sasuke.jpg'}
    
    mock_catalog_service.get_catalog.return_value = {
        'lookup': [item1, item2],
        'title_to_full_data': {'Naruto': item1, 'Sasuke': item2}
    }
    
    # Simuler Naruto -> Sasuke comme voisin proche
    mock_similarity_service.find_similar_items.return_value = {
        'metadatas': [[item2]]
    }
    
    res = undercover_service.start_game('Anime', 'Normal', ['P1', 'P2'], {'Anime': {'Normal': 100}})
    
    assert 'civil_word' in res
    assert 'undercover_word' in res
    assert len(res['assignments']) == 2
    assert any(a['role'] == 'Undercover' for a in res['assignments'].values())
    assert any(a['role'] == 'Civil' for a in res['assignments'].values())
