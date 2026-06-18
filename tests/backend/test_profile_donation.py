import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_client(db, api_client):
    user = User.objects.create_user(username="testuser", email="test@animetix.com")
    api_client.force_authenticate(user=user)
    return user, api_client


@pytest.mark.django_db
def test_claim_donation(user_client):
    user, client = user_client
    profile = user.profile

    # Init state
    assert "Sponsor Or" not in profile.unlocked_badges
    assert not profile.custom_username_color

    # Claim donation
    res = client.post("/api/v1/profiles/claim_donation/")
    assert res.status_code == 200
    assert "Sponsor Or" in res.data["unlocked_badges"]
    assert res.data["custom_username_color"] == "#FFD700"

    # Refresh DB check
    profile.refresh_from_db()
    assert "Sponsor Or" in profile.unlocked_badges
    assert profile.custom_username_color == "#FFD700"


@pytest.mark.django_db
def test_update_settings_without_donation(user_client):
    user, client = user_client

    # Try updating color without "Sponsor Or" badge
    res = client.patch(
        "/api/v1/profiles/update_settings/",
        {"custom_username_color": "#FF0000"},
        format="json",
    )
    assert res.status_code == 403
    assert "Vous devez soutenir le serveur" in res.data["error"]


@pytest.mark.django_db
def test_update_settings_with_donation_success(user_client):
    user, client = user_client
    profile = user.profile
    profile.unlocked_badges = ["Sponsor Or"]
    profile.save()

    # Update color - valid format
    res = client.patch(
        "/api/v1/profiles/update_settings/",
        {"custom_username_color": "#FF66B2"},
        format="json",
    )
    assert res.status_code == 200
    assert res.data["custom_username_color"] == "#FF66B2"

    profile.refresh_from_db()
    assert profile.custom_username_color == "#FF66B2"

    # Reset color
    res = client.patch(
        "/api/v1/profiles/update_settings/",
        {"custom_username_color": ""},
        format="json",
    )
    assert res.status_code == 200
    assert res.data["custom_username_color"] is None


@pytest.mark.django_db
def test_update_settings_invalid_color_format(user_client):
    user, client = user_client
    profile = user.profile
    profile.unlocked_badges = ["Sponsor Or"]
    profile.save()

    # Update color - invalid formats
    res = client.patch(
        "/api/v1/profiles/update_settings/",
        {"custom_username_color": "red"},
        format="json",
    )
    assert res.status_code == 400
    assert "Invalid color format" in res.data["error"]

    res = client.patch(
        "/api/v1/profiles/update_settings/",
        {"custom_username_color": "#FFFF"},
        format="json",
    )
    assert res.status_code == 400

    res = client.patch(
        "/api/v1/profiles/update_settings/",
        {"custom_username_color": "123456"},
        format="json",
    )
    assert res.status_code == 400
