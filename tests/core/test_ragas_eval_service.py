import pytest
from unittest.mock import MagicMock, patch
from core.domain.services.ragas_eval_service import RagasEvalService

@pytest.fixture
def mock_engine():
    return MagicMock()

@pytest.fixture
def eval_service(mock_engine):
    mock_pm = MagicMock()
    mock_pm.get_prompt.return_value = ("prompt", "system")
    return RagasEvalService(judge_engine=mock_engine, prompt_manager=mock_pm)

def test_evaluate_response_success(eval_service, mock_engine):
    # Mock scores (strings that will be converted to floats)
    mock_engine.generate.side_effect = ["0.8", "0.9", "1"]
    
    with patch("animetix.models.AIREvalResult.objects.create") as mock_create:
        res = eval_service.evaluate_response("q", "c", "r")
        assert res["faithfulness"] == 0.8
        assert res["answer_relevancy"] == 0.9
        assert res["context_precision"] == 1.0
        mock_create.assert_called_once()

def test_score_faithfulness_fallback(eval_service, mock_engine):
    mock_engine.generate.return_value = "invalid"
    assert eval_service._score_faithfulness("c", "r") == 0.5

def test_score_precision_fallback(eval_service, mock_engine):
    mock_engine.generate.return_value = "error"
    assert eval_service._score_precision("q", "c") == 0.0
