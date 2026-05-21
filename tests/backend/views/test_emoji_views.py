import pytest
from django.urls import reverse
from django.test import Client
from unittest.mock import MagicMock

@pytest.fixture
def client():
    return Client()

@pytest.fixture(autouse=True)
def mock_emoji_views_service(mock_container, mocker):
    """
    Autouse fixture that patches the local 'animetix_service' reference inside 
    animetix.views.emoji to delegate calls to mock_container.
    """
    mock_service = MagicMock()
    mock_service.load_data.return_value = {
        'titles': ['Naruto'], 
        'lookup': [{'title': 'Naruto', 'id': '1'}], 
        'title_to_full_data': {'Naruto': {'title': 'Naruto', 'id': '1', 'description': 'Ninja'}},
        'title_to_index': {'Naruto': 0},
        'db': [{'title': 'Naruto', 'id': '1'}]
    }
    
    # Delegate service attributes to the mock container's mocked services
    mock_service.emoji_service = mock_container.emoji_service
    mock_service.game_service = mock_container.game_service
    
    mocker.patch('animetix.views.emoji.animetix_service', mock_service)
    return mock_service

@pytest.mark.django_db
def test_emoji_decode_view_get(client, mock_container):
    """Vérifie le chargement de la page Emoji Decode."""
    # Mock emoji service methods on mock_container
    mock_container.emoji_service.select_secret.return_value = 'Naruto'
    mock_container.emoji_service.generate_emojis.return_value = ['🍥', '🦊', '⚡']

    url = reverse('emoji_decode')
    response = client.get(url)
    
    assert response.status_code == 200
    assert response.context['emojis'] == ['🍥', '🦊', '⚡']

@pytest.mark.django_db
def test_emoji_decode_guess_correct(client, mock_container):
    """Vérifie qu'une bonne réponse au décodage d'emoji termine le jeu."""
    # Mock services on mock_container
    mock_container.game_service.check_title_match.return_value = True
    
    # Set up session
    session = client.session
    session['emoji_secret'] = 'Naruto'
    session['emoji_guesses'] = []
    session['emoji_game_over'] = False
    session.save()
    
    url = reverse('emoji_guess')
    response = client.post(url, {'guess': 'Naruto'})
    
    assert response.status_code == 302 # Redirects to emoji_decode
    assert client.session['emoji_game_over'] is True
    assert len(client.session['emoji_guesses']) == 1
    assert client.session['emoji_guesses'][0]['is_correct'] is True
