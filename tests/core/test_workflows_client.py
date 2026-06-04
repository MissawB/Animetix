import pytest
from unittest.mock import MagicMock, patch
from adapters.inference.workflows_client import GCPWorkflowsClient

@patch('adapters.inference.workflows_client.ExecutionsClient')
def test_workflows_client_trigger_and_status(mock_executions_client):
    mock_instance = MagicMock()
    mock_executions_client.return_value = mock_instance
    
    mock_exec_response = MagicMock()
    mock_exec_response.name = "projects/test-proj/locations/test-loc/workflows/test-wf/executions/exec-123"
    mock_instance.create_execution.return_value = mock_exec_response
    
    mock_status_response = MagicMock()
    mock_status_response.state = 2 # SUCCEEDED
    mock_status_response.result = '{"status": "success", "translated_text": "Bonjour", "audio_url": "http://gcs/audio.wav"}'
    mock_status_response.error = None
    mock_instance.get_execution.return_value = mock_status_response

    client = GCPWorkflowsClient()
    client.project_id = "test-proj"
    client.parent = "projects/test-proj/locations/europe-west1/workflows/manga-voice-pipeline"
    
    exec_name = client.trigger_pipeline("img_b64", "audio_b64", "French", "out.wav")
    assert exec_name == "projects/test-proj/locations/test-loc/workflows/test-wf/executions/exec-123"
    
    status = client.get_execution_status(exec_name)
    assert status["state"] == "SUCCEEDED"
    assert status["result"]["translated_text"] == "Bonjour"
