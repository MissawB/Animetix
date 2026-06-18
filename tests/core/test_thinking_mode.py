from unittest.mock import MagicMock
from core.domain.services.llm_service import LLMService

from core.domain.entities.ai_schemas import InferenceResponse, InferenceMetadata


def test_llm_service_propagation():
    """Test that LLMService propagates thinking_mode to the engine."""
    mock_engine = MagicMock()
    mock_engine.generate.return_value = InferenceResponse(
        text="Response",
        metadata=InferenceMetadata(usage={"prompt_tokens": 10, "completion_tokens": 5}),
    )
    mock_pm = MagicMock()
    service = LLMService(inference_engine=mock_engine, prompt_manager=mock_pm)

    service.generate("test prompt", thinking_mode=True)

    # Verify propagation
    mock_engine.generate.assert_called_with(
        "test prompt", "", thinking_budget=0, thinking_mode=True, include_logprobs=True
    )
