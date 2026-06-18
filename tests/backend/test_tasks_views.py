import pytest
from django.urls import reverse
from unittest.mock import patch, MagicMock


@pytest.mark.django_db
@patch("animetix.tasks_views.GCPWorkflowsClient")
def test_poll_workflow_endpoint(mock_client_class, client):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    # Test ACTIVE state returns 503 Service Unavailable
    mock_client.get_execution_status.return_value = {
        "state": "ACTIVE",
        "error": None,
        "result": None,
    }

    url = reverse("poll-workflow")
    response = client.post(
        url,
        {"execution_name": "exec-123", "task_id": "t-123"},
        content_type="application/json",
    )
    assert response.status_code == 503

    # Test SUCCEEDED state returns 200 and stores in cache
    mock_client.get_execution_status.return_value = {
        "state": "SUCCEEDED",
        "error": None,
        "result": {"translated_text": "Bonjour", "audio_url": "http://gcs/audio.wav"},
    }
    response = client.post(
        url,
        {"execution_name": "exec-123", "task_id": "t-123"},
        content_type="application/json",
    )
    assert response.status_code == 200


@patch("animetix.containers.get_container")
def test_process_gcs_upload_task_dev_mode(mock_get_container):
    from animetix.creative_tasks import process_gcs_upload_task  # noqa: E402

    mock_manga_flow = MagicMock()
    mock_manga_flow.translate_manga_page.return_value = (
        "data:image/jpeg;base64,/9j/4AAQSkZJRg=="
    )

    mock_container = MagicMock()
    mock_container.manga_flow_service.return_value = mock_manga_flow
    mock_get_container.return_value = mock_container

    res = process_gcs_upload_task(bucket="test-bucket", name="raw-manga/page_01.png")
    assert res["status"] == "success"
    assert "translated-manga/page_01.png" in res["processed_path"]
    mock_manga_flow.translate_manga_page.assert_called_once()


@patch("animetix.tasks_views.id_token")
@patch("animetix.tasks_views.enqueue_task")
def test_eventarc_gcs_upload_endpoint_success(mock_enqueue, mock_id_token, client):
    from django.conf import settings  # noqa: E402

    url = reverse("eventarc-gcs-upload")

    # Mock OIDC in production
    with patch.object(settings, "IS_PRODUCTION", True):
        headers = {"HTTP_AUTHORIZATION": "Bearer token-123"}
        payload = {"bucket": "my-bucket", "name": "raw-manga/page_01.png"}

        response = client.post(url, payload, content_type="application/json", **headers)
        assert response.status_code == 200
        assert response.json()["status"] == "event processed"
        mock_enqueue.assert_called_once_with(
            "process_gcs_upload_task", bucket="my-bucket", name="raw-manga/page_01.png"
        )


@pytest.mark.django_db
def test_eventarc_gcs_upload_endpoint_missing_payload(client):
    url = reverse("eventarc-gcs-upload")
    # Missing parameters should return 400
    response = client.post(url, {}, content_type="application/json")
    assert response.status_code == 400
    assert "Missing bucket or name" in response.json()["error"]


@pytest.mark.django_db
@patch("animetix.tasks_views.enqueue_task")
def test_eventarc_gcs_upload_endpoint_non_manga_ignored(mock_enqueue, client):
    url = reverse("eventarc-gcs-upload")
    # File that is not a manga page should be ignored (no task enqueued, but return 200)
    payload = {"bucket": "my-bucket", "name": "other_stuff/document.pdf"}
    response = client.post(url, payload, content_type="application/json")
    assert response.status_code == 200
    mock_enqueue.assert_not_called()
