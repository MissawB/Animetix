import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import MagicMock
from animetix.containers import container
from dependency_injector import providers
from animetix.models import CreativeFusion
from django.contrib.auth.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def mock_user(db):
    user = User.objects.create_user(username="testuser", password="password")
    return user


@pytest.fixture
def other_user(db):
    user = User.objects.create_user(username="otheruser", password="password")
    return user


@pytest.fixture
def sample_fusion(db, mock_user):
    return CreativeFusion.objects.create(
        title_a="Anime A",
        title_b="Anime B",
        media_type_a="Anime",
        media_type_b="Anime",
        scenario_text="Un scénario épique.",
        creator=mock_user,
    )


@pytest.mark.django_db
class TestForgeVNAPI:
    def test_get_vn_script(self, api_client, sample_fusion):
        url = reverse("api_forge_vn", kwargs={"fusion_id": sample_fusion.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["vn_script"] is None

    def test_generate_vn_script_unauthorized(
        self, api_client, other_user, sample_fusion
    ):
        api_client.force_authenticate(user=other_user)
        url = reverse("api_forge_vn", kwargs={"fusion_id": sample_fusion.id})
        data = {"action": "generate"}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_generate_vn_script_success(
        self, api_client, mock_user, sample_fusion, mock_container
    ):
        api_client.force_authenticate(user=mock_user)
        url = reverse("api_forge_vn", kwargs={"fusion_id": sample_fusion.id})
        data = {"action": "generate"}

        mock_script_data = {
            "title": "Fusion Script",
            "scenes": [
                {
                    "character": "Protagonist",
                    "text": "Hello world",
                    "mood": "Happy",
                    "bg_prompt": "Forest",
                }
            ],
        }

        # Create a mock that behaves like a Pydantic model
        class MockScript:
            def model_dump(self):
                return mock_script_data

        # Configure the global mock_container
        mock_container.visual_novel_service.generate_script.return_value = MockScript()
        mock_container.visual_novel_service.return_value.generate_script.return_value = MockScript()

        mock_guardrail = MagicMock()
        mock_guardrail.validate_input.return_value = {"is_safe": True}
        mock_guardrail.validate_output.return_value = {"is_safe": True}

        mock_usage = MagicMock()
        mock_usage.check_quota.return_value = True

        with (
            container.core.visual_novel_service.override(
                providers.Object(mock_container.visual_novel_service)
            ),
            container.core.guardrail_service.override(providers.Object(mock_guardrail)),
            container.infrastructure.usage_port.override(providers.Object(mock_usage)),
        ):
            response = api_client.post(url, data, format="json")
            assert response.status_code == status.HTTP_200_OK
            assert response.data["vn_script"]["title"] == "Fusion Script"

            # Verify persistence
            sample_fusion.refresh_from_db()
            assert sample_fusion.vn_script["title"] == "Fusion Script"

    def test_update_vn_script_success(self, api_client, mock_user, sample_fusion):
        api_client.force_authenticate(user=mock_user)
        url = reverse("api_forge_vn", kwargs={"fusion_id": sample_fusion.id})

        new_script = {"title": "Updated Title", "scenes": []}
        data = {"action": "update", "vn_script": new_script}

        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["vn_script"]["title"] == "Updated Title"

        sample_fusion.refresh_from_db()
        assert sample_fusion.vn_script["title"] == "Updated Title"
