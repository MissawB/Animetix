import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from animetix.models import AITokenUsage

@pytest.mark.django_db
def test_refill_quota_endpoint():
    user = User.objects.create_user(username="testaduser", password="password123")
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Créer un usage pour aujourd'hui
    AITokenUsage.objects.create(
        user=user,
        engine="gpt-4o",
        input_tokens=1000,
        output_tokens=2000,
        total_tokens=3000,
        cost_estimate=0.05
    )
    
    # Vérifier que l'usage existe
    assert AITokenUsage.objects.filter(user=user).count() == 1
    
    # Appeler refill_quota
    url = "/api/v1/profiles/refill_quota/"
    response = client.post(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "refilled"
    assert response.data["deleted_records"] == 1
    
    # Vérifier que l'usage a été supprimé
    assert AITokenUsage.objects.filter(user=user).count() == 0
