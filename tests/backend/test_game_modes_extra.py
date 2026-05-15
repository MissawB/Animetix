import pytest
from django.urls import reverse
from django.test import Client

@pytest.fixture
def client():
    return Client()

@pytest.mark.django_db
def test_classic_game_flow(client, mock_animetix_service):
    """Test le mode classique : affichage, proposition, victoire."""
    mock_animetix_service.load_data.return_value = {
        'titles': ['Naruto', 'One Piece'],
        'title_to_full_data': {'Naruto': {'id': 1}, 'One Piece': {'id': 2}},
        'title_to_index': {'Naruto': 0, 'One Piece': 1},
        'autocomplete_json': '[]',
        'db': [],
        'lookup': [{'title': 'Naruto'}, {'title': 'One Piece'}]
    }
    
    # 1. Start new game
    response = client.get(reverse('start_game'))
    assert response.status_code == 302 # Redirect to /game/
    assert client.session.get('secret_title') is not None
    
    # 2. Make a guess
    response = client.post(reverse('make_guess'), {'guess': 'Naruto'})
    assert response.status_code == 302
    assert len(client.session.get('guesses', [])) == 1

@pytest.mark.django_db
def test_akinetix_flow(client, mock_animetix_service):
    mock_animetix_service.load_data.return_value = {
        'titles': ['Naruto'],
        'title_to_full_data': {'Naruto': {'id': 1}},
        'autocomplete_json': '[]',
        'db': [],
        'lookup': [{'title': 'Naruto'}]
    }
    url = reverse('akinetix')
    response = client.get(url)
    assert response.status_code == 200
    
    # Submit answer
    response = client.post(reverse('akinetix_answer'), {'answer': 'yes'})
    assert response.status_code == 302

@pytest.mark.django_db
def test_animinator_flow(client, mock_animetix_service):
    mock_animetix_service.load_data.return_value = {
        'titles': ['Naruto'],
        'title_to_full_data': {'Naruto': {'id': 1}},
        'autocomplete_json': '[]',
        'db': [],
        'lookup': [{'title': 'Naruto'}]
    }
    url = reverse('animinator')
    response = client.get(url)
    assert response.status_code == 200
    
    # Submit answer
    response = client.post(reverse('animinator_ask'), {'question': 'Is he a ninja?'})
    assert response.status_code == 302

@pytest.mark.django_db
def test_vision_quest_flow(client, mock_animetix_service):
    mock_animetix_service.load_data.return_value = {
        'titles': ['Naruto'],
        'title_to_full_data': {'Naruto': {'id': 1, 'image': 'n.jpg', 'title': 'Naruto'}},
        'autocomplete_json': '[]',
        'db': [{'id': 1, 'title': 'Naruto', 'image': 'n.jpg'}],
        'lookup': [{'title': 'Naruto'}]
    }
    url = reverse('vision_quest')
    response = client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_archetypist_flow(client, mock_animetix_service):
    mock_animetix_service.load_data.return_value = {
        'titles': ['Naruto', 'Sasuke'],
        'title_to_full_data': {'Naruto': {}, 'Sasuke': {}},
        'autocomplete_json': '[]',
        'db': [],
        'lookup': [{'title': 'Naruto'}, {'title': 'Sasuke'}]
    }
    url = reverse('archetypist')
    response = client.get(url)
    assert response.status_code == 200
