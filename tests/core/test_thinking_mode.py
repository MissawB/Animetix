import pytest
from unittest.mock import MagicMock, patch
from core.domain.services.llm_service import LLMService

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
