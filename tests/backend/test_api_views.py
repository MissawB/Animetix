import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from animetix.models import DailyChallenge, Achievement
from django.contrib.auth.models import User

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client(api_client):
    user = User.objects.create_user(username='testuser', password='password')
    api_client.force_authenticate(user=user)
    return api_client

@pytest.mark.django_db
def test_profile_me_endpoint(authenticated_client):
    """Vérifie que l'utilisateur peut récupérer son propre profil."""
    url = reverse('profile-me')
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert response.data['user']['username'] == 'testuser'

@pytest.mark.django_db
def test_daily_challenge_list(api_client):
    """Vérifie la liste des défis quotidiens."""
    DailyChallenge.objects.create(date='2026-05-03', media_type='Anime', secret_title='Naruto')
    url = reverse('dailychallenge-list')
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.data) >= 1
    assert response.data[0]['secret_title'] == 'Naruto'

@pytest.mark.django_db
def test_media_search_empty_query(api_client, mocker):
    """Vérifie la recherche média sans query (retourne les plus populaires)."""
    # Mocker le service pour éviter de charger ChromaDB en test
    mock_service = mocker.patch('animetix.api_views.animetix_service')
    mock_service.load_data.return_value = {
        'lookup': [{'title': 'One Piece', 'id': 1}, {'title': 'Bleach', 'id': 2}]
    }
    
    url = reverse('media-search')
    response = api_client.get(url, {'media_type': 'Anime', 'limit': 1})
    
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['title'] == 'One Piece'

@pytest.mark.django_db
def test_media_search_with_query(api_client, mocker):
    """Vérifie le filtrage de la recherche média par titre."""
    mock_service = mocker.patch('animetix.api_views.animetix_service')
    mock_service.load_data.return_value = {
        'lookup': [{'title': 'Dragon Ball', 'id': 1}, {'title': 'Naruto', 'id': 2}]
    }
    
    url = reverse('media-search')
    response = api_client.get(url, {'q': 'Dragon'})
    
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['title'] == 'Dragon Ball'
