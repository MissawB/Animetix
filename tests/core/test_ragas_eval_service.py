import pytest
from unittest.mock import MagicMock, patch
from core.domain.services.ragas_eval_service import RagasEvalService

@pytest.fixture
def mock_engine():
    return MagicMock()

@pytest.fixture
def eval_service(mock_engine):
    return RagasEvalService(judge_engine=mock_engine)

def test_evaluate_response_success(eval_service, mock_engine):
    # Mock Ragas evaluate result
    mock_result = {
        "faithfulness": 0.8,
        "answer_relevancy": 0.9,
        "context_precision": 1.0
    }
    
    with patch("core.domain.services.ragas_eval_service.evaluate", return_value=mock_result) as mock_evaluate:
        res = eval_service.evaluate_response("q", "c", "r")
        assert res["faithfulness"] == 0.8
        assert res["answer_relevancy"] == 0.9
        assert res["context_precision"] == 1.0
        mock_evaluate.assert_called_once()

def test_evaluate_response_failure(eval_service, mock_engine):
    with patch("core.domain.services.ragas_eval_service.evaluate", side_effect=Exception("Ragas error")):
        res = eval_service.evaluate_response("q", "c", "r")
        assert res["faithfulness"] == 0.0
        assert res["answer_relevancy"] == 0.0
        assert res["context_precision"] == 0.0

def test_run_batch_evaluation_no_gold_port(eval_service):
    res = eval_service.run_batch_evaluation()
    assert res == {}

def test_run_batch_evaluation_success(mock_engine):
    mock_gold = MagicMock()
    mock_gold.get_all_entries.return_value = [
        {"question": "q1", "context": "c1", "answer": "a1", "ground_truth": "gt1"}
    ]
    
    service = RagasEvalService(judge_engine=mock_engine, gold_port=mock_gold)
    
    mock_result = {
        "faithfulness": 0.7,
        "answer_relevancy": 0.6,
        "context_precision": 0.5
    }
    
    with patch("core.domain.services.ragas_eval_service.evaluate", return_value=mock_result):
        res = service.run_batch_evaluation()
        assert res["faithfulness"] == 0.7
        assert res["answer_relevancy"] == 0.6
        assert res["context_precision"] == 0.5
