import pytest
from unittest.mock import MagicMock
from core.domain.services.reasoning_agent_service import ReasoningAgentService

@pytest.fixture
def mock_engine():
    return MagicMock()

@pytest.fixture
def mock_search():
    return MagicMock()

@pytest.fixture
def reasoning_agent(mock_engine, mock_search):
    return ReasoningAgentService(inference_engine=mock_engine, search_service=mock_search)

def test_solve_complex_query_search_path(reasoning_agent, mock_engine, mock_search):
    mock_engine.generate.side_effect = [
        "THOUGHT: I should search.\nACTION: SEARCH", # Thought
        "The final answer." # Final Answer
    ]
    mock_search.hybrid_search.return_value = [{'title': 'Naruto', 'description': '...'}]
    
    ans = reasoning_agent.solve_complex_query("Who is Naruto?", "Anime")
    assert "The final answer." in ans
    assert "Naruto" in ans # Check sources appended

def test_solve_complex_query_no_action(reasoning_agent, mock_engine):
    mock_engine.generate.side_effect = [
        "THOUGHT: I know this.\nACTION: ANSWER", 
        "It is a show."
    ]
    ans = reasoning_agent.solve_complex_query("What is Anime?", "Anime")
    assert ans == "It is a show."

def test_on_bus_message(reasoning_agent):
    # Smoke test for callback
    mock_bus = MagicMock()
    reasoning_agent.agent_bus = mock_bus
    reasoning_agent._on_bus_message("msg1")
    mock_bus.read_shared_memory.assert_called_once_with("msg1")
