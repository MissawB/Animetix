import pytest
from unittest.mock import MagicMock
from adapters.persistence.session_state_adapter import DjangoSessionStateAdapter
from core.domain.services.game_session_service import GameSessionService
from animetix.presenters import GamePresenter

class MockSession:
    def __init__(self):
        self.data = {}
        self.modified = False
    def __getitem__(self, key): return self.data[key]
    def __setitem__(self, key, value): self.data[key] = value
    def get(self, key, default=None): return self.data.get(key, default)
    def update(self, data): self.data.update(data)
    def __contains__(self, key): return key in self.data

@pytest.fixture
def mock_request():
    request = MagicMock()
    request.session = MockSession()
    return request

def test_session_service_classic_start(mock_request):
    port = DjangoSessionStateAdapter(mock_request.session)
    service = GameSessionService(port)
    service.start_classic_game("Naruto", "Normal", "Anime")
    
    assert mock_request.session.data['secret_title'] == "Naruto"
    assert mock_request.session.data['game_over'] is False
    assert mock_request.session.data['guesses'] == []
    assert mock_request.session.modified is True

def test_session_service_add_guess(mock_request):
    port = DjangoSessionStateAdapter(mock_request.session)
    service = GameSessionService(port)
    mock_request.session.data['guesses'] = []
    
    guess = {"title": "One Piece", "score": 85.0}
    service.add_guess(guess)
    
    assert len(mock_request.session.data['guesses']) == 1
    assert mock_request.session.data['guesses'][0]['title'] == "One Piece"
    assert mock_request.session.modified is True

def test_game_presenter_score_color():
    presenter = GamePresenter()
    assert presenter.get_score_color(95) == "danger"
    assert presenter.get_score_color(75) == "warning"
    assert presenter.get_score_color(50) == "primary"
    assert presenter.get_score_color(10) == "secondary"

def test_game_presenter_format_hint():
    presenter = GamePresenter()
    hint = presenter.format_hint("desc", "Description", 10, "A boy with a tail", 15, ["desc"])
    
    assert hint['label'] == "Description"
    assert hint['revealed'] is True
    assert hint['value'] == "A boy with a tail"
    assert hint['can_reveal'] is True

def test_game_presenter_format_hint_locked():
    presenter = GamePresenter()
    hint = presenter.format_hint("desc", "Description", 20, "Hidden", 10, [])
    
    assert hint['revealed'] is False
    assert hint['can_reveal'] is False
    assert hint['value'] is None
