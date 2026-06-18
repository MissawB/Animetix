from unittest.mock import MagicMock, patch
from adapters.inference.qwen3_vl_adapter import Qwen3VLAdapter


@patch("adapters.inference.qwen3_vl_adapter.InferenceClient")
def test_video_analysis_calls_hf_api(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    # Mock response structure for InferenceClient.chat_completion
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Episode 12"
    mock_client.chat_completion.return_value = mock_response

    adapter = Qwen3VLAdapter(token="fake_token")
    result = adapter.localize_video_actions(b"fake_video_data", ["Which episode?"])

    assert "Episode 12" in result[0]["answer"]
