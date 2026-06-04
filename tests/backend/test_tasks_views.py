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
