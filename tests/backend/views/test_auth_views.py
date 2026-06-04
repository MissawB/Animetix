import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.test import Client

@pytest.fixture
def client():
    return Client()

@pytest.mark.django_db
def test_auth_me_unauthenticated(client):
    url = reverse('api_auth_me')
    response = client.get(url)
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.django_db
def test_auth_me_authenticated(client):
    user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
    client.force_login(user)
    
    url = reverse('api_auth_me')
    response = client.get(url)
    
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"] == user.id
    assert data["user"]["username"] == "testuser"
    assert data["user"]["email"] == "test@example.com"
