import pytest
from unittest.mock import MagicMock
from core.domain.services.llm_service import LLMService

from core.domain.entities.ai_schemas import InferenceResponse


@pytest.fixture
def mock_engine():
    return MagicMock()


@pytest.fixture
def mock_prompt_manager():
    pm = MagicMock()
    pm.get_prompt.return_value = ("Test prompt", "Test system")
    return pm


@pytest.fixture
def llm_service(mock_engine, mock_prompt_manager):
    return LLMService(inference_engine=mock_engine, prompt_manager=mock_prompt_manager)


def test_explain_relationship(llm_service, mock_engine, mock_prompt_manager):
    mock_prompt_manager.get_prompt.return_value = (
        "Explique de manière concise pourquoi 'Naruto' et 'Ninja' sont liés par la relation 'HAS_THEME'.",
        "System prompt",
    )
    mock_engine.generate.return_value = InferenceResponse(
        text="Parce que Naruto est un ninja."
    )

    result = llm_service.explain_relationship("Naruto", "Ninja", "HAS_THEME")

    assert result == "Parce que Naruto est un ninja."

    mock_prompt_manager.get_prompt.assert_called_once_with(
        "explain_link", source_name="Naruto", target_name="Ninja", rel_type="HAS_THEME"
    )

    mock_engine.generate.assert_called_once_with(
        "Explique de manière concise pourquoi 'Naruto' et 'Ninja' sont liés par la relation 'HAS_THEME'.",
        "System prompt",
        thinking_budget=0,
        thinking_mode=False,
        include_logprobs=True,
    )
