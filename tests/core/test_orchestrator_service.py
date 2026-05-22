import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from core.domain.services.orchestrator_agent_service import OrchestratorAgentService, State

@pytest.fixture
def mock_engine():
    engine = MagicMock()
    engine.generate.return_value = '{"complexity_score": 1, "thinking_budget": 50}'
    return engine

@pytest.fixture
def mock_factory():
    factory = MagicMock()
    factory.uncertainty_service.measure_confidence.return_value = {"is_reliable": True, "confidence_score": 0.9}
    return factory

@pytest.fixture
def orchestrator(mock_engine, mock_factory):
    mock_pm = MagicMock()
    mock_pm.get_prompt.return_value = ("prompt", "system")
    return OrchestratorAgentService(inference_engine=mock_engine, services_factory=mock_factory, prompt_manager=mock_pm)

@pytest.mark.asyncio
async def test_execute_workflow_simple(orchestrator, mock_engine):
    # Node PLANNER (json), Node VERIFIER (str), Node WRITER (str)
    mock_engine.generate.side_effect = [
        '{"next_node": "RETRIEVER", "plan": []}', # PLANNER
        'OUI', # VERIFIER
        'Final answer.' # WRITER
    ]
    
    ans = await orchestrator.execute_workflow("Query", "Anime")
    assert ans == 'Final answer.'

@pytest.mark.asyncio
async def test_execute_workflow_full_path(orchestrator, mock_engine, mock_factory):
    # Node PLANNER, Node VERIFIER, Node WRITER
    mock_engine.generate.side_effect = [
        '{"next_node": "RETRIEVER", "plan": ["search"]}', # PLANNER
        'OUI', # VERIFIER
        'Final answer.' # WRITER
    ]
    
    ans = await orchestrator.execute_workflow("Complex Query", "Manga")
    assert ans == 'Final answer.'

@pytest.mark.asyncio
async def test_writer_low_confidence_retry(orchestrator, mock_engine, mock_factory):
    # 1st Loop: PLANNER, VERIFIER, WRITER
    # 2nd Loop: VERIFIER (called after RETRIEVER), WRITER
    mock_engine.generate.side_effect = [
        '{"next_node": "RETRIEVER"}', # Loop 1: PLANNER
        'OUI', # Loop 1: VERIFIER
        'First attempt.', # Loop 1: WRITER
        'OUI', # Loop 2: VERIFIER
        'Better answer.'  # Loop 2: WRITER
    ]
    
    # First writer call is low confidence, second is high
    mock_factory.uncertainty_service.measure_confidence.side_effect = [
        {"confidence_score": 0.3, "is_reliable": False},
        {"confidence_score": 0.9, "is_reliable": True}
    ]
    
    ans = await orchestrator.execute_workflow("Query", "Anime")
    assert ans == 'Better answer.'
