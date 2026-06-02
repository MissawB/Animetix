import pytest
from unittest.mock import MagicMock
from core.domain.services.ragas_eval_service import RagasEvalService, EvaluationResult

@pytest.fixture
def mock_engine():
    return MagicMock()

@pytest.fixture
def eval_service(mock_engine):
    return RagasEvalService(judge_engine=mock_engine)

def test_evaluate_response_success(eval_service, mock_engine):
    mock_result = EvaluationResult(
        faithfulness=0.8,
        answer_relevancy=0.9,
        context_precision=1.0,
        context_recall=None
    )
    mock_engine.generate_structured.return_value = mock_result
    
    res = eval_service.evaluate_response("q", "c", "r")
    assert res["faithfulness"] == 0.8
    assert res["answer_relevancy"] == 0.9
    assert res["context_precision"] == 1.0
    mock_engine.generate_structured.assert_called_once()

def test_evaluate_response_failure(eval_service, mock_engine):
    mock_engine.generate_structured.side_effect = Exception("LLM error")
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
    
    mock_result = EvaluationResult(
        faithfulness=0.7,
        answer_relevancy=0.6,
        context_precision=0.5,
        context_recall=0.4
    )
    mock_engine.generate_structured.return_value = mock_result
    
    res = service.run_batch_evaluation()
    assert res["faithfulness"] == 0.7
    assert res["answer_relevancy"] == 0.6
    assert res["context_precision"] == 0.5
    assert res["context_recall"] == 0.4

def test_evaluate_response_with_persistence_no_hallucination(mock_engine):
    mock_eval_port = MagicMock()
    service = RagasEvalService(judge_engine=mock_engine, eval_port=mock_eval_port)
    
    mock_result = EvaluationResult(
        faithfulness=0.8,
        answer_relevancy=0.9,
        context_precision=1.0,
        context_recall=None
    )
    mock_engine.generate_structured.return_value = mock_result
    
    res = service.evaluate_response("What is the prompt?", "The prompt is simple.", "It is simple.")
    
    assert res["faithfulness"] == 0.8
    mock_eval_port.save_result.assert_called_once_with(
        "What is the prompt?",
        "The prompt is simple.",
        "It is simple.",
        {
            "faithfulness": 0.8,
            "answer_relevance": 0.9,
            "context_precision": 1.0,
            "hallucination": False
        }
    )

def test_evaluate_response_with_persistence_and_hallucination(mock_engine):
    mock_eval_port = MagicMock()
    service = RagasEvalService(judge_engine=mock_engine, eval_port=mock_eval_port)
    
    mock_result = EvaluationResult(
        faithfulness=0.3,
        answer_relevancy=0.5,
        context_precision=0.4,
        context_recall=None
    )
    mock_engine.generate_structured.return_value = mock_result
    
    res = service.evaluate_response("Query", "Context", "Hallucinated Answer")
    
    assert res["faithfulness"] == 0.3
    mock_eval_port.save_result.assert_called_once_with(
        "Query",
        "Context",
        "Hallucinated Answer",
        {
            "faithfulness": 0.3,
            "answer_relevance": 0.5,
            "context_precision": 0.4,
            "hallucination": True
        }
    )

def test_run_batch_evaluation_partial_entries(mock_engine):
    mock_gold = MagicMock()
    # First entry is incomplete (missing answer), second is complete
    mock_gold.get_all_entries.return_value = [
        {"question": "q1", "context": "c1", "ground_truth": "gt1"},
        {"question": "q2", "context": "c2", "answer": "a2", "ground_truth": "gt2"}
    ]
    
    service = RagasEvalService(judge_engine=mock_engine, gold_port=mock_gold)
    
    mock_result = EvaluationResult(
        faithfulness=0.9,
        answer_relevancy=0.8,
        context_precision=0.7,
        context_recall=0.6
    )
    mock_engine.generate_structured.return_value = mock_result
    
    res = service.run_batch_evaluation()
    
    assert res["faithfulness"] == 0.9
    assert res["answer_relevancy"] == 0.8
    # Only the second entry should have been evaluated
    assert mock_engine.generate_structured.call_count == 1

def test_run_batch_evaluation_item_failure(mock_engine):
    mock_gold = MagicMock()
    # Two valid entries
    mock_gold.get_all_entries.return_value = [
        {"question": "q1", "context": "c1", "answer": "a1", "ground_truth": "gt1"},
        {"question": "q2", "context": "c2", "answer": "a2", "ground_truth": "gt2"}
    ]
    
    service = RagasEvalService(judge_engine=mock_engine, gold_port=mock_gold)
    
    # LLM fails on the first, but succeeds on the second
    mock_result = EvaluationResult(
        faithfulness=0.8,
        answer_relevancy=0.8,
        context_precision=0.8,
        context_recall=0.8
    )
    mock_engine.generate_structured.side_effect = [Exception("LLM Timeout"), mock_result]
    
    res = service.run_batch_evaluation()
    
    # The batch should successfully complete by averaging over the only valid result (1 entry)
    assert res["faithfulness"] == 0.8
    assert res["answer_relevancy"] == 0.8
    assert mock_engine.generate_structured.call_count == 2

