from unittest.mock import MagicMock

import pytest
from animetix.containers import container
from dependency_injector import providers
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(autouse=True)
def mock_guardrail_service():
    mock_guard = MagicMock()
    mock_guard.validate_input.return_value = {"is_safe": True}
    mock_guard.validate_output.return_value = {"is_safe": True}
    with container.core.guardrail_service.override(providers.Object(mock_guard)):
        yield mock_guard


@pytest.fixture
def mock_user(db):
    from django.contrib.auth.models import User  # noqa: E402

    user = User.objects.create_user(username="testuser", password="password")
    return user


@pytest.mark.django_db
class TestCompanionAPI:
    def test_companion_interact_authenticated_only(self, api_client):
        url = reverse("api_companion_interact")
        response = api_client.post(url, {})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_companion_interact_success(self, api_client, mock_user):
        api_client.force_authenticate(user=mock_user)
        url = reverse("api_companion_interact")

        data = {
            "mentor_id": "sensei",
            "user_message": "Hello Sensei!",
            "context_url": "http://example.com",
        }

        # We need to mock CompanionService and UsagePort
        mock_companion_service = MagicMock()
        mock_companion_service.generate_response.return_value = "Response from Sensei"

        mock_usage_port = MagicMock()
        mock_usage_port.check_quota.return_value = True

        with (
            container.core.companion_service.override(
                providers.Object(mock_companion_service)
            ),
            container.infrastructure.usage_port.override(
                providers.Object(mock_usage_port)
            ),
        ):
            response = api_client.post(url, data, format="json")

            assert response.status_code == status.HTTP_200_OK
            assert response.data["response"] == "Response from Sensei"
            assert "history" in response.data
            # Verify history was updated in session
            assert len(response.data["history"]) == 2  # user + assistant

    def test_companion_interact_quota_exceeded(self, api_client, mock_user):
        api_client.force_authenticate(user=mock_user)
        url = reverse("api_companion_interact")

        mock_usage_port = MagicMock()
        mock_usage_port.check_quota.return_value = False

        with container.infrastructure.usage_port.override(
            providers.Object(mock_usage_port)
        ):
            response = api_client.post(
                url, {"mentor_id": "sensei", "user_message": "msg"}, format="json"
            )
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "quota" in response.data["error"].lower()
