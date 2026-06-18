from unittest.mock import MagicMock

import pytest
from core.domain.entities.ai_schemas import CritiqueResult
from core.domain.exceptions import InferenceError
from core.domain.services.rag.agents.critic import ResponseCritic


@pytest.fixture
def mock_llm():
    return MagicMock()


@pytest.fixture
def mock_pm():
    pm = MagicMock()
    pm.get_prompt.return_value = ("critic prompt", "critic system")
    return pm


def test_critic_evaluate_success(mock_llm, mock_pm):
    agent = ResponseCritic(llm_service=mock_llm, prompt_manager=mock_pm)
    mock_llm.generate.return_value = '{"is_relevant": true, "relevance_score": 0.85, "suggested_action": "PROCEED", "missing_info": ""}'

    res = agent.evaluate("neon genesis evangelion", "Eva is a giant robot anime.")

    assert isinstance(res, CritiqueResult)
    assert res.is_relevant is True
    assert res.relevance_score == 0.85


def test_critic_evaluate_malformed_json(mock_llm, mock_pm):
    agent = ResponseCritic(llm_service=mock_llm, prompt_manager=mock_pm)
    mock_llm.generate.return_value = "No JSON here!"

    res = agent.evaluate("neon genesis evangelion", "Eva is a giant robot anime.")

    assert isinstance(res, CritiqueResult)
    assert res.is_relevant is False
    assert res.relevance_score == 0.0
    assert "Malformed" in res.missing_info or "contained JSON" in res.missing_info


def test_critic_evaluate_inference_error(mock_llm, mock_pm):
    agent = ResponseCritic(llm_service=mock_llm, prompt_manager=mock_pm)
    mock_llm.generate.side_effect = InferenceError("Timeout contacting model")

    res = agent.evaluate("neon genesis evangelion", "Eva is a giant robot anime.")

    assert isinstance(res, CritiqueResult)
    assert res.is_relevant is False
    assert res.relevance_score == 0.0
    assert "Erreur d'inférence" in res.missing_info


def test_critic_evaluate_unexpected_error(mock_llm, mock_pm):
    agent = ResponseCritic(llm_service=mock_llm, prompt_manager=mock_pm)
    mock_llm.generate.side_effect = ValueError("Some unexpected error")

    res = agent.evaluate("neon genesis evangelion", "Eva is a giant robot anime.")

    assert isinstance(res, CritiqueResult)
    assert res.is_relevant is False
    assert res.relevance_score == 0.0
    assert "Unexpected failure" in res.missing_info
