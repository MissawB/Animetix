import pytest
from unittest.mock import MagicMock, patch
from pydantic import BaseModel
from adapters.inference.unified_inference_adapter import UnifiedInferenceAdapter
from core.domain.exceptions import InferenceError

class User(BaseModel):
    name: str
    age: int

def test_unified_generate_structured_success():
    adapter = UnifiedInferenceAdapter(api_base="http://localhost:11434/v1", model_name="qwen3.5")
    
    mock_user_json = '{"name": "Test User", "age": 25}'
    from core.domain.entities.ai_schemas import InferenceResponse
    
    with patch.object(adapter, "generate", return_value=InferenceResponse(text=mock_user_json)) as mock_generate:
        result = adapter.generate_structured(
            prompt="Extract user info",
            response_model=User
        )
        
        assert isinstance(result, User)
        assert result.name == "Test User"
        assert result.age == 25
        mock_generate.assert_called()

def test_unified_generate_structured_retry_logic():
    adapter = UnifiedInferenceAdapter(api_base="http://localhost:11434/v1", model_name="qwen3.5")
    from core.domain.entities.ai_schemas import InferenceResponse
    
    # First call fails (invalid JSON), second succeeds
    with patch.object(adapter, "generate", side_effect=[
        InferenceResponse(text="Invalid JSON"),
        InferenceResponse(text='{"name": "Retry User", "age": 40}')
    ]) as mock_generate:
        result = adapter.generate_structured(
            prompt="Extract user info",
            response_model=User
        )
        
        assert result.name == "Retry User"
        assert mock_generate.call_count == 2

def test_unified_generate_structured_failure():
    adapter = UnifiedInferenceAdapter(api_base="http://localhost:11434/v1", model_name="qwen3.5")
    from core.domain.entities.ai_schemas import InferenceResponse
    
    with patch.object(adapter, "generate", return_value=InferenceResponse(text="Still not JSON")):
        with pytest.raises(Exception) as exc_info:
            adapter.generate_structured(
                prompt="Extract user info",
                response_model=User,
                max_retries=2
            )
        assert "generate_structured failed" in str(exc_info.value)
