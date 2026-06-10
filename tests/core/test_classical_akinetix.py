import pytest
from unittest.mock import MagicMock
from core.domain.services.akinetix_service import AkinetixService

@pytest.fixture
def sample_db():
    return [
        {'id': '1', 'title': 'Naruto', 'genres': ['Action'], 'micro_tags': ['ninja']},
        {'id': '2', 'title': 'One Piece', 'genres': ['Adventure'], 'micro_tags': ['pirate']}
    ]

@pytest.fixture
def catalog_service():
    mock_service = MagicMock()
    mock_service.get_akinetix_attributes.return_value = {}
    return mock_service

def test_classical_akinetix_init(sample_db, catalog_service):
    service = AkinetixService(catalog_service=catalog_service, catalog_db=sample_db)
    assert service.n_items == 2
    assert 'genre:Action' in service.attributes

def test_update_probabilities_yes(sample_db, catalog_service):
    service = AkinetixService(catalog_service=catalog_service, catalog_db=sample_db)
    service.update_probabilities('genre:Action', 'yes')
    probs = service.get_probabilities()
    assert probs['Naruto'] > probs['One Piece']

def test_update_probabilities_no(sample_db, catalog_service):
    service = AkinetixService(catalog_service=catalog_service, catalog_db=sample_db)
    service.update_probabilities('genre:Action', 'no')
    probs = service.get_probabilities()
    assert probs['One Piece'] > probs['Naruto']

def test_propose_next_question(sample_db, catalog_service):
    service = AkinetixService(catalog_service=catalog_service, catalog_db=sample_db)
    q = service.propose_next_question()
    assert q in service.attributes

def test_format_question(sample_db, catalog_service):
    service = AkinetixService(catalog_service=catalog_service, catalog_db=sample_db)
    assert "Action" in service.format_question('genre:Action')

def test_get_best_guess(sample_db, catalog_service):
    service = AkinetixService(catalog_service=catalog_service, catalog_db=sample_db)
    service.update_probabilities('tag:ninja', 'yes')
    title, prob = service.get_best_guess()
    assert title == 'Naruto'
    assert prob > 0.5
    
def test_fine_attributes_usage(sample_db, catalog_service):
    fine_attrs = {'1': {'is_hokage': True}, '2': {'is_hokage': False}}
    catalog_service.get_akinetix_attributes.return_value = fine_attrs
    service = AkinetixService(catalog_service=catalog_service, catalog_db=sample_db)
    assert 'fine:is_hokage' in service.attributes
    service.update_probabilities('fine:is_hokage', 'yes')
    title, _ = service.get_best_guess()
    assert title == 'Naruto'
