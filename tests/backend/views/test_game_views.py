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
def test_blindtest_guess_correct(client, mock_container):
    """Vérifie qu'une bonne réponse au Blind Test fonctionne."""
    # Setup session
    session = client.session
    session['blindtest_secret'] = 'Naruto'
    session['blindtest_guesses'] = []
    session['blindtest_game_over'] = False
    session.save()

    # Configure the shared mock from container
    mock_container.game_service.check_title_match.return_value = True

    url = reverse('blindtest_guess')
    response = client.post(url, {'guess': 'Naruto'})
    
    assert response.status_code == 302 # Redirect to game page
    
    # Reload session to see changes
    final_session = client.session
    assert final_session.get('blindtest_game_over') is True
    assert final_session.get('blindtest_guesses')[0]['is_correct'] is True

@pytest.mark.django_db
def test_covertest_view_get(client, mock_container):
    """Vérifie le chargement de la page Cover Test."""
    url = reverse('covertest')
    response = client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_covertest_guess_wrong(client, mock_container):
    """Vérifie qu'une mauvaise réponse au Cover Test est enregistrée."""
    session = client.session
    session['covertest_secret'] = 'Naruto'
    session['covertest_guesses'] = []
    session['covertest_game_over'] = False
    session.save()
    
    # Configure shared mock
    mock_container.game_service.check_title_match.return_value = False
    
    url = reverse('covertest_guess')
    response = client.post(url, {'guess': 'Bleach'})
    
    assert response.status_code == 302
    
    final_session = client.session
    assert final_session.get('covertest_game_over') is False
    assert len(final_session.get('covertest_guesses', [])) > 0
    assert final_session['covertest_guesses'][0]['is_correct'] is False
