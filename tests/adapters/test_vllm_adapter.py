import pytest
from unittest.mock import MagicMock, patch
from adapters.inference.vllm_adapter import VllmAdapter
from pydantic import BaseModel

class UserProfile(BaseModel):
    name: str
    age: int

def test_vllm_generate_structured():
    adapter = VllmAdapter(api_base="http://test-url", model_name="test-model")
    
    mock_instructor = MagicMock()
    mock_openai_lib = MagicMock()
    mock_client = MagicMock()
    
    mock_instructor.from_openai.return_value = mock_client
    
    expected_response = UserProfile(name="John Doe", age=30)
    mock_client.chat.completions.create.return_value = expected_response
    
    with patch.dict("sys.modules", {"instructor": mock_instructor, "openai": mock_openai_lib}):
        # We also need to mock OpenAI class specifically if it's imported from openai
        mock_openai_lib.OpenAI = MagicMock()
        
        result = adapter.generate_structured(
            prompt="Tell me about John Doe",
            response_model=UserProfile,
            system_prompt="You are a helper"
        )
        
        assert result == expected_response
        mock_instructor.from_openai.assert_called_once()
        mock_client.chat.completions.create.assert_called_once_with(
            model="test-model",
            response_model=UserProfile,
            messages=[
                {"role": "system", "content": "You are a helper"},
                {"role": "user", "content": "Tell me about John Doe"}
            ],
            max_retries=3
        )

def test_vllm_generate_structured_error():
    adapter = VllmAdapter(api_base="http://test-url", model_name="test-model")
    
    mock_instructor = MagicMock()
    mock_openai_lib = MagicMock()
    mock_client = MagicMock()
    
    mock_instructor.from_openai.return_value = mock_client
    mock_client.chat.completions.create.side_effect = Exception("API Error")
    
    with patch.dict("sys.modules", {"instructor": mock_instructor, "openai": mock_openai_lib}):
        mock_openai_lib.OpenAI = MagicMock()
        
        with pytest.raises(Exception) as excinfo:
            adapter.generate_structured(
                prompt="Fail",
                response_model=UserProfile
            )
        assert "API Error" in str(excinfo.value)
