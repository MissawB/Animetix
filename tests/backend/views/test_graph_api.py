import pytest
from django.urls import reverse
from unittest.mock import MagicMock
from django.contrib.auth.models import User

@pytest.fixture
def premium_user(db):
    user = User.objects.create_user(username='premium_user', password='password')
    user.profile.tier = 'premium'
    user.profile.save()
    return user

@pytest.fixture
def free_user(db):
    user = User.objects.create_user(username='free_user', password='password')
    user.profile.tier = 'free'
    user.profile.save()
    return user

@pytest.mark.django_db
def test_graph_neighbors_premium_access(client, premium_user, mock_container):
    client.force_login(premium_user)
    
    # Mock the return value of get_neighborhood
    mock_data = {"nodes": [{"id": "1"}], "links": []}
    mock_container.graph_persistence_port.get_neighborhood.return_value = mock_data
    
    from animetix.containers import container
    from dependency_injector import providers
    with container.graph_persistence_port.override(providers.Object(mock_container.graph_persistence_port)):
        url = reverse('api_graph_neighbors')
        response = client.get(url, {'id': '123', 'type': 'Anime', 'depth': 2})
        
        assert response.status_code == 200
        assert response.json() == mock_data
        mock_container.graph_persistence_port.get_neighborhood.assert_called_once_with('123', 'Anime', 2)

@pytest.mark.django_db
def test_graph_neighbors_free_denied(client, free_user, mock_container):
    client.force_login(free_user)
    
    url = reverse('api_graph_neighbors')
    response = client.get(url, {'id': '123', 'type': 'Anime'})
    
    assert response.status_code == 403
    assert "Premium" in response.json()['error']

@pytest.mark.django_db
def test_graph_neighbors_unauthenticated_denied(client):
    url = reverse('api_graph_neighbors')
    response = client.get(url, {'id': '123', 'type': 'Anime'})
    
    # DRF returns 403 if permission_classes = [IsAuthenticated] and not logged in
    # but since it's an API, it might return 401 depending on authentication settings.
    # Default DRF behavior for SessionAuthentication/BasicAuthentication is 403 for Forbidden if CSRF fails,
    # or 403 for Not Authenticated if not provided.
    assert response.status_code in [401, 403]

@pytest.mark.django_db
def test_graph_neighbors_missing_params(client, premium_user):
    client.force_login(premium_user)
    
    url = reverse('api_graph_neighbors')
    response = client.get(url, {'id': '123'}) # missing type
    
    assert response.status_code == 400
    assert "required" in response.json()['error']

@pytest.mark.django_db
def test_graph_neighbors_invalid_depth(client, premium_user):
    client.force_login(premium_user)
    
    url = reverse('api_graph_neighbors')
    response = client.get(url, {'id': '123', 'type': 'Anime', 'depth': 'invalid'})
    
    assert response.status_code == 400
    assert "integer" in response.json()['error']
