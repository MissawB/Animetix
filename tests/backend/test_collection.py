import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth.models import User
from animetix.models import CreativeFusion, Profile

@pytest.mark.django_db
def test_toggle_collection():
    user = User.objects.create_user(username="collector", password="pwd")
    # Profile is auto-created by signal
    fusion = CreativeFusion.objects.create(
        title_a="A", title_b="B", media_type_a="Anime", media_type_b="Anime", scenario_text="Test"
    )
    
    client = Client()
    client.force_login(user)
    
    # Add to collection
    response = client.post(reverse('toggle_collection', args=[fusion.id]))
    assert response.status_code == 200
    assert fusion in user.profile.collected_fusions.all()
    
    # Remove from collection
    response = client.post(reverse('toggle_collection', args=[fusion.id]))
    assert response.status_code == 200
    assert fusion not in user.profile.collected_fusions.all()
