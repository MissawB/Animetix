import pytest
from unittest.mock import MagicMock
from core.domain.services.orchestrator_agent_service import OrchestratorAgentService, State

@pytest.fixture
def mock_engine():
    engine = MagicMock()
    engine.generate.return_value = '{"plan": [], "next_node": "WRITER"}'
    return engine

@pytest.fixture
def mock_factory():
    factory = MagicMock()
    factory.agentic_rag.plan_and_solve.return_value = "RAG Result"
    factory.uncertainty_service.measure_confidence.return_value = {"confidence_score": 0.9, "is_reliable": True}
    return factory

@pytest.fixture
def orchestrator(mock_engine, mock_factory):
    return OrchestratorAgentService(inference_engine=mock_engine, services_factory=mock_factory)

def test_execute_workflow_simple(orchestrator, mock_engine):
    mock_engine.generate.side_effect = [
        '{"plan": ["p"], "next_node": "WRITER"}', # Planner
        'The final answer.' # Writer
    ]
    ans = orchestrator.execute_workflow("What is Naruto?", "Anime")
    assert ans == 'The final answer.'
    assert mock_engine.generate.call_count == 2

def test_execute_workflow_full_path(orchestrator, mock_engine, mock_factory):
    mock_engine.generate.side_effect = [
        '{"plan": ["p"], "next_node": "RETRIEVER"}', # Planner
        'OUI', # Verifier (is reliable?)
        'Final result.' # Writer
    ]
    ans = orchestrator.execute_workflow("Query", "Anime")
    assert ans == 'Final result.'
    mock_factory.agentic_rag.plan_and_solve.assert_called_once()

def test_writer_low_confidence_retry(orchestrator, mock_engine, mock_factory):
    mock_engine.generate.side_effect = [
        '{"plan": [], "next_node": "WRITER"}', # Step 1: Planner
        'Bad answer.', # Step 2: Writer
        '{"plan": [], "next_node": "WRITER"}', # Step 3: Planner (re-called by next node dispatch in loop?) 
        # Wait, the loop will re-run Planner if next_node is PLANNER.
        # But WRITER sets next_node to RETRIEVER if low confidence.
        'Better answer.' # Step 5: Writer
    ]
    # Configure factory to return low confidence first
    mock_factory.uncertainty_service.measure_confidence.side_effect = [
        {"confidence_score": 0.3, "is_reliable": False},
        {"confidence_score": 0.9, "is_reliable": True}
    ]
    
    ans = orchestrator.execute_workflow("Query", "Anime")
    assert ans == 'Better answer.'
