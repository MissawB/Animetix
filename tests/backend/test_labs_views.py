from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.urls import reverse


@pytest.fixture
def user(db):
    return User.objects.create_user(username="test_user", password="password")


@pytest.mark.integration  # Boots the full production stack (live LLM, GCP, pgvector).
@pytest.mark.django_db
@patch("animetix.api.labs.GCPWorkflowsClient")
def test_manga_voice_endpoint_production(
    mock_workflows_client_class, client, settings, user
):
    client.force_login(user)
    settings.IS_PRODUCTION = True
    mock_client = MagicMock()
    mock_workflows_client_class.return_value = mock_client
    mock_client.trigger_pipeline.return_value = (
        "projects/test/locations/europe-west1/workflows/wf/executions/ex-123"
    )

    url = reverse("manga-voice")
    response = client.post(
        url,
        {
            "image": "b64_image_content",
            "reference_audio": "b64_audio_content",
            "target_lang": "French",
        },
        content_type="application/json",
    )

    assert response.status_code == 202
    assert "task_id" in response.json()
    assert mock_client.enqueue_polling_task.called


@pytest.mark.django_db
def test_manga_voice_endpoint_local_dev(client, settings, user):
    client.force_login(user)
    settings.IS_PRODUCTION = False

    url = reverse("manga-voice")
    response = client.post(
        url,
        {
            "image": "b64_image_content",
            "reference_audio": "b64_audio_content",
            "target_lang": "French",
        },
        content_type="application/json",
    )

    assert response.status_code == 202
    assert "task_id" in response.json()
