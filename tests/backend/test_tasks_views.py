import pytest
from django.urls import reverse
from unittest.mock import patch, MagicMock

@pytest.mark.django_db
@patch('animetix.tasks_views.GCPWorkflowsClient')
def test_poll_workflow_endpoint(mock_client_class, client):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Test ACTIVE state returns 503 Service Unavailable
    mock_client.get_execution_status.return_value = {"state": "ACTIVE", "error": None, "result": None}
    
    url = reverse('poll-workflow')
    response = client.post(url, {"execution_name": "exec-123", "task_id": "t-123"}, content_type="application/json")
    assert response.status_code == 503
    
    # Test SUCCEEDED state returns 200 and stores in cache
    mock_client.get_execution_status.return_value = {
        "state": "SUCCEEDED",
        "error": None,
        "result": {
            "translated_text": "Bonjour",
            "audio_url": "http://gcs/audio.wav"
        }
    }
    response = client.post(url, {"execution_name": "exec-123", "task_id": "t-123"}, content_type="application/json")
    assert response.status_code == 200

@patch('animetix.containers.get_container')
def test_process_gcs_upload_task_dev_mode(mock_get_container):
    from animetix.creative_tasks import process_gcs_upload_task
    mock_manga_flow = MagicMock()
    mock_manga_flow.translate_manga_page.return_value = "data:image/jpeg;base64,/9j/4AAQSkZJRg=="
    
    mock_container = MagicMock()
    mock_container.manga_flow_service.return_value = mock_manga_flow
    mock_get_container.return_value = mock_container

    res = process_gcs_upload_task(bucket="test-bucket", name="raw-manga/page_01.png")
    assert res["status"] == "success"
    assert "translated-manga/page_01.png" in res["processed_path"]
    mock_manga_flow.translate_manga_page.assert_called_once()

