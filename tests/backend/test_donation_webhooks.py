import json
import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from animetix.models import Donation, Achievement, UserAchievement
from adapters.persistence.django_donation_adapter import DjangoDonationAdapter
from adapters.persistence.django_achievement_adapter import DjangoAchievementAdapter
from core.domain.services.achievement_service import AchievementDomainService

@pytest.fixture(autouse=True)
def setup_mock_container(mock_container):
    """Inject real adapters into the mock container for these tests."""
    mock_container.health_dashboard_service.donation_port = DjangoDonationAdapter()
    mock_container.achievement_service = AchievementDomainService(port=DjangoAchievementAdapter())
    return mock_container

@pytest.mark.django_db
def test_donation_webhook_anonymous(client):
    url = reverse('donation_webhook')
    data = {
        'amount': '10.00',
        'currency': 'USD',
        'message_id': 'tr_123',
        'email': 'anon@example.com'
    }
    response = client.post(url, data=json.dumps(data), content_type='application/json')
    
    assert response.status_code == 200
    assert Donation.objects.filter(transaction_id='tr_123').exists()

@pytest.mark.django_db
def test_donation_webhook_unlocked_achievement(client):
    user = User.objects.create_user(username='mécène', email='donor@example.com')
    # S'assurer que les achievements existent
    Achievement.objects.create(code='donor_bronze', name='Bronze', icon='☕')
    
    url = reverse('donation_webhook')
    data = {
        'amount': '5.00',
        'currency': 'USD',
        'message_id': 'tr_456',
        'email': 'donor@example.com'
    }
    response = client.post(url, data=json.dumps(data), content_type='application/json')
    
    assert response.status_code == 200
    assert UserAchievement.objects.filter(user=user, achievement__code='donor_bronze').exists()
