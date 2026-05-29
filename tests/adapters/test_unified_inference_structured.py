import pytest
from unittest.mock import MagicMock, patch
from pydantic import BaseModel
from adapters.inference.unified_inference_adapter import UnifiedInferenceAdapter
from core.domain.exceptions import InferenceError
import instructor

class User(BaseModel):
    name: str
    age: int

def test_unified_generate_structured_success():
    adapter = UnifiedInferenceAdapter(api_base="http://localhost:11434/v1", model_name="llama3")
    
    mock_user = User(name="Test User", age=25)
    
    with patch("instructor.from_openai") as mock_from_openai:
        mock_client = MagicMock()
        mock_from_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_user
        
        result = adapter.generate_structured(
            prompt="Extract user info",
            response_model=User
        )
        
        assert result == mock_user
        mock_from_openai.assert_called_once()
        args, kwargs = mock_from_openai.call_args
        assert kwargs["mode"] == instructor.Mode.JSON

def test_unified_generate_structured_fallback_success():
    adapter = UnifiedInferenceAdapter(api_base="http://localhost:11434/v1", model_name="llama3")
    
    with patch("instructor.from_openai", side_effect=Exception("Instructor missing")):
        with patch.object(adapter, "generate", return_value='{"name": "Fallback User", "age": 30}') as mock_generate:
            result = adapter.generate_structured(
                prompt="Extract user info",
                response_model=User
            )
            
            assert isinstance(result, User)
            assert result.name == "Fallback User"
            assert result.age == 30
            mock_generate.assert_called_once_with("Extract user info", system_prompt="", json_mode=True)

def test_unified_generate_structured_fallback_failure():
    adapter = UnifiedInferenceAdapter(api_base="http://localhost:11434/v1", model_name="llama3")
    
    with patch("instructor.from_openai", side_effect=Exception("Instructor missing")):
        with patch.object(adapter, "generate", return_value="Not a JSON string"):
            with pytest.raises(InferenceError) as exc_info:
                adapter.generate_structured(
                    prompt="Extract user info",
                    response_model=User
                )
            assert "Structured generation failed" in str(exc_info.value)
