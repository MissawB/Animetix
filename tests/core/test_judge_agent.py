from unittest.mock import MagicMock

import pytest
from core.domain.entities.ai_schemas import JudgeEvaluation
from core.domain.services.rag.agents.judge import ResponseJudge


@pytest.fixture
def mock_llm():
    return MagicMock()


@pytest.fixture
def mock_pm():
    pm = MagicMock()
    pm.get_prompt.return_value = ("judge prompt", "judge system")
    return pm


def test_judge_evaluate_success(mock_llm, mock_pm):
    agent = ResponseJudge(llm_service=mock_llm, prompt_manager=mock_pm)

    mock_llm.generate.return_value = '{"is_reliable": true, "faithfulness_score": 0.9, "relevancy_score": 1.0, "hallucination_detected": false, "reasoning": "Great answer.", "next_action": "APPROVE"}'

    res = agent.evaluate(
        "Who is Naruto?",
        "Naruto is a ninja.",
        "Naruto is the main character and a ninja.",
    )

    assert isinstance(res, JudgeEvaluation)
    assert res.is_reliable is True
    assert res.faithfulness_score == 0.9


def test_judge_evaluate_parsing_error(mock_llm, mock_pm):
    agent = ResponseJudge(llm_service=mock_llm, prompt_manager=mock_pm)

    # Invalid JSON
    mock_llm.generate.return_value = "This is not JSON."

    res = agent.evaluate("Q", "C", "A")
    assert isinstance(res, JudgeEvaluation)
    assert res.next_action == "REWRITE"
    assert "Invalid or empty response" in res.reasoning


def test_judge_evaluate_with_obs_service(mock_llm, mock_pm):
    mock_obs = MagicMock()
    agent = ResponseJudge(
        llm_service=mock_llm, prompt_manager=mock_pm, obs_service=mock_obs
    )

    mock_llm.generate.return_value = '{"is_reliable": true, "faithfulness_score": 1.0, "relevancy_score": 1.0, "hallucination_detected": false, "reasoning": "ok", "next_action": "APPROVE"}'

    agent.evaluate("Q", "C", "A")

    # Verify dynamic eval was logged
    mock_obs.log_dynamic_eval.assert_called_once()
