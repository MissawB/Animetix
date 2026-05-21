import pytest
from unittest.mock import MagicMock
from src.core.domain.services.akinetix_service import AkinetixDomainService

@pytest.fixture
def sample_db():
    return [
        {'id': '1', 'title': 'Naruto', 'genres': ['Action'], 'micro_tags': ['ninja']},
        {'id': '2', 'title': 'One Piece', 'genres': ['Adventure'], 'micro_tags': ['pirate']}
    ]

@pytest.fixture
def mock_catalog():
    service = MagicMock()
    service.get_akinetix_attributes.return_value = {
        '1': {'is_hokage': True},
        '2': {'is_hokage': False}
    }
    return service

def test_akinetix_service_start_game(sample_db, mock_catalog):
    domain_service = AkinetixDomainService(catalog_service=mock_catalog)
    state = domain_service.start_new_game(sample_db)
    
    assert state['game_over'] is False
    assert state['ai_guess'] is None
    assert 'current_q' in state
    assert 'probs' in state
    assert len(state['probs']) == 2
    assert 'asked_attrs' in state
    mock_catalog.get_akinetix_attributes.assert_called_once()

def test_akinetix_service_process_answer(sample_db, mock_catalog):
    domain_service = AkinetixDomainService(catalog_service=mock_catalog)
    
    # 1. Start game
    state = domain_service.start_new_game(sample_db)
    
    # 2. Process answer
    new_state = domain_service.process_answer(sample_db, state, 'OUI')
    
    assert len(new_state['history']) == 1
    assert new_state['history'][0]['a'] == 'OUI'
    assert 'probs' in new_state
    
    # 3. Repeat and test game over condition
    # Force game over by making probs highly skewed
    new_state['probs'] = [0.95, 0.05]
    new_state['asked_attrs'] = ['genre:Action', 'genre:Adventure', 'genre:Comedy', 'genre:Drama', 'genre:Sci-Fi']
    
    final_state = domain_service.process_answer(sample_db, new_state, 'OUI')
    assert final_state['game_over'] is True
    assert final_state['ai_guess'] == 'Naruto'
    assert "Est-ce que tu penses à : Naruto ?" in final_state['current_q']
