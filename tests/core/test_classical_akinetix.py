import pytest
import numpy as np
from core.domain.services.akinetix_classical_service import ClassicalAkinetixService
from core.domain.services.akinetix.question_formatter import QuestionFormatter

@pytest.fixture
def sample_db():
    return [
        {'id': '1', 'title': 'Naruto', 'genres': ['Action'], 'micro_tags': ['ninja']},
        {'id': '2', 'title': 'One Piece', 'genres': ['Adventure'], 'micro_tags': ['pirate']}
    ]

@pytest.fixture
def formatter():
    return QuestionFormatter()

def test_classical_akinetix_init(sample_db, formatter):
    service = ClassicalAkinetixService(sample_db, formatter=formatter)
    assert service.n_items == 2
    assert 'genre:Action' in service.attributes

def test_update_probabilities_yes(sample_db, formatter):
    service = ClassicalAkinetixService(sample_db, formatter=formatter)
    service.update_probabilities('genre:Action', 'yes')
    probs = service.get_probabilities()
    assert probs['Naruto'] > probs['One Piece']

def test_update_probabilities_no(sample_db, formatter):
    service = ClassicalAkinetixService(sample_db, formatter=formatter)
    service.update_probabilities('genre:Action', 'no')
    probs = service.get_probabilities()
    assert probs['One Piece'] > probs['Naruto']

def test_propose_next_question(sample_db, formatter):
    service = ClassicalAkinetixService(sample_db, formatter=formatter)
    q = service.propose_next_question()
    assert q in service.attributes

def test_format_question(sample_db, formatter):
    service = ClassicalAkinetixService(sample_db, formatter=formatter)
    assert "Action" in service.format_question('genre:Action')

def test_get_best_guess(sample_db, formatter):
    service = ClassicalAkinetixService(sample_db, formatter=formatter)
    service.update_probabilities('tag:ninja', 'yes')
    title, prob = service.get_best_guess()
    assert title == 'Naruto'
    assert prob > 0.5
    
def test_fine_attributes_usage(sample_db, formatter):
    fine_attrs = {'1': {'is_hokage': True}, '2': {'is_hokage': False}}
    service = ClassicalAkinetixService(sample_db, fine_attributes=fine_attrs, formatter=formatter)
    assert 'fine:is_hokage' in service.attributes
    service.update_probabilities('fine:is_hokage', 'yes')
    title, _ = service.get_best_guess()
    assert title == 'Naruto'
