import pytest
from unittest.mock import MagicMock, patch
from adapters.inference.vllm_adapter import VllmAdapter
from adapters.inference.gguf_adapter import GgufAdapter
from core.domain.services.llm_service import LLMService

@patch('requests.post')
def test_vllm_adapter_thinking_mode(mock_post):
    """Test that VllmAdapter correctly passes thinking_mode in the payload."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'choices': [{'message': {'content': 'Thinking response'}}]
    }
    mock_post.return_value = mock_response

    adapter = VllmAdapter(api_base="http://test:8000/v1", model_name="test-model")
    adapter.generate("test prompt", thinking_mode=True)

    # Verify that thinking_mode was passed in the JSON payload
    args, kwargs = mock_post.call_args
    payload = kwargs['json']
    assert payload['extra_body']['thinking_mode'] is True

def test_gguf_adapter_thinking_mode():
    """Test that GgufAdapter injects the <think> block when thinking_mode is True."""
    adapter = GgufAdapter(model_path="fake/path")
    # Mock llama-cpp model
    mock_llm = MagicMock()
    mock_llm.create_chat_completion.return_value = {
        'choices': [{'message': {'content': 'GGUF response'}}]
    }
    adapter.llm = mock_llm

    adapter.generate("test prompt", system_prompt="System instructions", thinking_mode=True)

    # Verify that <think> was injected into the system prompt
    args, kwargs = mock_llm.create_chat_completion.call_args
    system_msg = [m for m in kwargs['messages'] if m['role'] == 'system'][0]
    assert "<think>" in system_msg['content']
    assert "Analyse la requête en profondeur" in system_msg['content']

def test_llm_service_propagation():
    """Test that LLMService propagates thinking_mode to the engine."""
    mock_engine = MagicMock()
    mock_pm = MagicMock()
    service = LLMService(inference_engine=mock_engine, prompt_manager=mock_pm)

    service.generate("test prompt", thinking_mode=True)

    # Verify propagation
    mock_engine.generate.assert_called_with(
        "test prompt", 
        "", 
        thinking_budget=0, 
        thinking_mode=True
    )
