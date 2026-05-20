import pytest
from unittest.mock import MagicMock
from pydantic import BaseModel
from src.adapters.inference.fallback_adapter import FallbackInferenceAdapter

class User(BaseModel):
    name: str
    age: int

def test_fallback_generate_structured_success():
    mock_adapter1 = MagicMock()
    mock_adapter1.generate_structured.side_effect = Exception("Failed")
    
    mock_adapter2 = MagicMock()
    mock_user = User(name="Test User", age=25)
    mock_adapter2.generate_structured.return_value = mock_user
    
    fallback = FallbackInferenceAdapter(adapters=[mock_adapter1, mock_adapter2])
    
    result = fallback.generate_structured(
        prompt="Extract user info",
        response_model=User
    )
    
    assert result == mock_user
    mock_adapter1.generate_structured.assert_called_once()
    mock_adapter2.generate_structured.assert_called_once()

def test_fallback_generate_structured_all_failed():
    mock_adapter1 = MagicMock()
    mock_adapter1.generate_structured.side_effect = Exception("Failed 1")
    
    mock_adapter2 = MagicMock()
    mock_adapter2.generate_structured.side_effect = Exception("Failed 2")
    
    fallback = FallbackInferenceAdapter(adapters=[mock_adapter1, mock_adapter2])
    
    with pytest.raises(Exception) as excinfo:
        fallback.generate_structured(
            prompt="Extract user info",
            response_model=User
        )
    
    assert "Tous les adaptateurs ont échoué" in str(excinfo.value)
