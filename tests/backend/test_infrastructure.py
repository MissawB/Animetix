import pytest
from unittest.mock import MagicMock
from src.backend.animetix.session_manager import GameSessionManager
from src.backend.animetix.presenters import GamePresenter

@pytest.fixture
def mock_request():
    request = MagicMock()
    request.session = {}
    return request

def test_session_manager_classic_start(mock_request):
    manager = GameSessionManager(mock_request)
    manager.start_classic_game("Naruto", "Normal", "Anime")
    
    assert mock_request.session['secret_title'] == "Naruto"
    assert mock_request.session['game_over'] is False
    assert mock_request.session['guesses'] == []

def test_session_manager_add_guess(mock_request):
    manager = GameSessionManager(mock_request)
    mock_request.session['guesses'] = []
    
    guess = {"title": "One Piece", "score": 85.0}
    manager.add_guess(guess)
    
    assert len(mock_request.session['guesses']) == 1
    assert mock_request.session['guesses'][0]['title'] == "One Piece"

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
