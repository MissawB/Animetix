import pytest
import httpx
from unittest.mock import patch, MagicMock
from adapters.inference.brain_api_adapter import BrainAPIAdapter
from core.domain.entities.ai_schemas import InferenceResponse, TokenLogProb

@pytest.fixture
def brain_adapter():
    return BrainAPIAdapter(brain_api_url="http://brain-api:5000")

def test_generate_returns_inference_response(brain_adapter):
    mock_response_data = {
        "text": "Hello world",
        "usage": {"prompt_tokens": 5, "completion_tokens": 2},
        "thinking": "Thinking about hello"
    }
    
    with patch("adapters.inference.brain_api_adapter.safe_http_request") as mock_request:
        mock_res = MagicMock()
        mock_res.json.return_value = mock_response_data
        mock_res.status_code = 200
        mock_request.return_value = mock_res
        
        response = brain_adapter.generate("Hi")
        
        assert isinstance(response, InferenceResponse)
        assert response.text == "Hello world"
        assert response.metadata.usage == {"prompt_tokens": 5, "completion_tokens": 2}
        assert response.metadata.thinking == "Thinking about hello"
        assert response.metadata.logprobs is None

def test_generate_with_logprobs(brain_adapter):
    mock_response_data = {
        "text": "Hello world",
        "usage": {"prompt_tokens": 5, "completion_tokens": 2},
        "logprobs": [
            {"token": "Hello", "logprob": -0.1},
            {"token": " world", "logprob": -0.05}
        ]
    }
    
    with patch("adapters.inference.brain_api_adapter.safe_http_request") as mock_request:
        mock_res = MagicMock()
        mock_res.json.return_value = mock_response_data
        mock_res.status_code = 200
        mock_request.return_value = mock_res
        
        response = brain_adapter.generate("Hi", include_logprobs=True)
        
        assert isinstance(response, InferenceResponse)
        assert len(response.metadata.logprobs) == 2
        assert response.metadata.logprobs[0].token == "Hello"
        assert response.metadata.logprobs[0].logprob == -0.1
        assert response.metadata.logprobs[1].token == " world"
        assert response.metadata.logprobs[1].logprob == -0.05

def test_stream_generate_yields_inference_response(brain_adapter):
    mock_response_data = {
        "text": "Hello world",
        "usage": {"prompt_tokens": 5, "completion_tokens": 2}
    }
    
    with patch("adapters.inference.brain_api_adapter.safe_http_request") as mock_request:
        mock_res = MagicMock()
        mock_res.json.return_value = mock_response_data
        mock_res.status_code = 200
        mock_request.return_value = mock_res
        
        generator = brain_adapter.stream_generate("Hi")
        response = next(generator)
        
        assert isinstance(response, InferenceResponse)
        assert response.text == "Hello world"
