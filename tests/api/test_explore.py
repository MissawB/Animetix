import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from animetix.models import UserRecommendation, MediaItem
from django.contrib.auth.models import User

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_media_explore_view_recommendations(api_client):
    user = User.objects.create_user(username='testuser', password='password')
    api_client.force_authenticate(user=user)
    
    # Créer un media et une recommandation
    media = MediaItem.objects.create(external_id="test-1", title="Test Media", media_type="Anime")
    UserRecommendation.objects.create(user=user, media_item=media, score=0.9, rank=1)
    
    url = reverse('api_explore')
    response = api_client.get(url, {'media_type': 'Anime'})
    
    assert response.status_code == status.HTTP_200_OK
    assert 'recommendations' in response.data
    assert len(response.data['recommendations']) > 0
    assert response.data['recommendations'][0]['id'] == "test-1"
