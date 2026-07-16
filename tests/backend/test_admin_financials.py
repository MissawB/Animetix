import pytest
from animetix.models import AdEvent, AITokenUsage
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_log_ad_event_success(api_client):
    res = api_client.post(
        "/api/v1/billing/log_ad_event/",
        {"event_type": "impression", "ad_type": "banner"},
        format="json",
    )
    assert res.status_code == 201
    assert AdEvent.objects.count() == 1
    event = AdEvent.objects.first()
    assert event.event_type == "impression"
    assert event.ad_type == "banner"


@pytest.mark.django_db
def test_log_ad_event_invalid(api_client):
    res = api_client.post(
        "/api/v1/billing/log_ad_event/",
        {"event_type": "invalid_event", "ad_type": "banner"},
        format="json",
    )
    assert res.status_code == 400


@pytest.fixture
def admin_client(db, api_client):
    admin_user = User.objects.create_superuser(
        username="admin", email="admin@animetix.com", password="password"
    )
    api_client.force_authenticate(user=admin_user)
    return admin_user, api_client


@pytest.mark.django_db
def test_admin_financials_permission_denied(api_client):
    # Anonymous client
    res = api_client.get("/api/v1/admin/financials/")
    assert res.status_code == 403


@pytest.mark.django_db
def test_admin_financials_success(admin_client):
    admin, client = admin_client

    # Create mock AI usage
    AITokenUsage.objects.create(
        engine="openai",
        input_tokens=100,
        output_tokens=100,
        total_tokens=200,
        cost_estimate=1.50,
    )
    AITokenUsage.objects.create(
        engine="replicate",
        input_tokens=100,
        output_tokens=100,
        total_tokens=200,
        cost_estimate=2.00,
    )

    # Create mock ad events
    AdEvent.objects.create(event_type="impression", ad_type="video")
    AdEvent.objects.create(event_type="impression", ad_type="banner")
    AdEvent.objects.create(event_type="click", ad_type="banner")

    # Create mock sponsor profile
    user2 = User.objects.create_user(username="sponsor_user", email="sponsor@test.com")
    profile = user2.profile
    profile.unlocked_badges = ["Sponsor Or"]
    profile.save()

    res = client.get("/api/v1/admin/financials/")
    assert res.status_code == 200
    data = res.data

    assert data["total_ai_cost"] == 3.50
    assert data["cost_by_engine"]["openai"] == 1.50
    assert data["cost_by_engine"]["replicate"] == 2.00
    assert data["ad_stats"]["video_impressions"] == 1
    assert data["ad_stats"]["banner_impressions"] == 1
    assert data["ad_stats"]["clicks"] == 1
    assert data["donation_stats"]["gold_sponsors"] == 1
    assert data["donation_stats"]["total_donations"] == 5.00
    assert data["estimated_ad_revenue"] == (1 * 0.003) + (1 * 0.001) + (1 * 0.15)
