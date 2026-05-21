import pytest
from django.urls import reverse
from django.test import Client
import json

@pytest.fixture
def client():
    return Client()

@pytest.mark.django_db
def test_blindtest_view_get(client, mock_animetix_service):
    """Vérifie le chargement de la page Blind Test."""
    url = reverse('blindtest')
    response = client.get(url)
    
    assert response.status_code == 200

@pytest.mark.django_db
def test_blindtest_guess_correct(client, mock_animetix_service):
    """Vérifie qu'une bonne réponse au Blind Test fonctionne."""
    # Setup session
    session = client.session
    session['blindtest_secret'] = 'Naruto'
    session['blindtest_guesses'] = []
    session.save()

    # Simulate correct guess
    mock_animetix_service.game_service.check_title_match.return_value = True

    url = reverse('blindtest_guess')
    response = client.post(url, {'guess': 'Naruto'})
    
    assert response.status_code == 302 # Redirect to game page
    assert client.session['blindtest_game_over'] is True
    assert client.session['blindtest_guesses'][0]['is_correct'] is True

@pytest.mark.django_db
def test_covertest_view_get(client, mock_animetix_service):
    """Vérifie le chargement de la page Cover Test."""
    url = reverse('covertest')
    response = client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_covertest_guess_wrong(client, mock_animetix_service):
    """Vérifie qu'une mauvaise réponse au Cover Test est enregistrée."""
    session = client.session
    session['covertest_secret'] = 'Naruto'
    session['covertest_guesses'] = []
    session['covertest_game_over'] = False
    session.save()
    
    # Simulate wrong guess
    mock_animetix_service.game_service.check_title_match.return_value = False
    
    url = reverse('covertest_guess')
    response = client.post(url, {'guess': 'Bleach'})
    
    assert response.status_code == 302
    assert client.session.get('covertest_game_over') is False
    assert client.session['covertest_guesses'][0]['is_correct'] is False
