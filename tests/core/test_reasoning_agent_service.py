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
def mock_prompts():
    pm = MagicMock()
    # Mock get_prompt to return a tuple (prompt, system_prompt)
    pm.get_prompt.return_value = ("mock prompt", "mock system")
    return pm

@pytest.fixture
def reasoning_agent(mock_engine, mock_prompts, mock_search):
    return ReasoningAgentService(inference_engine=mock_engine, prompt_manager=mock_prompts, search_service=mock_search)

def test_solve_complex_query_search_path(reasoning_agent, mock_engine, mock_search):
    mock_engine.generate.side_effect = [
        "THOUGHT: I should search.\nACTION: SEARCH\nPARAMS: Naruto", # Iteration 1
        "THOUGHT: I found info.\nACTION: ANSWER",                  # Iteration 2
        "The final answer about Naruto."                            # Final Answer (outside loop)
    ]
    mock_search.hybrid_search.return_value = [{'title': 'Naruto', 'description': '...'}]
    
    ans = reasoning_agent.solve_complex_query("Who is Naruto?", "Anime")
    assert "The final answer about Naruto." in ans
    assert "Naruto" in ans # Check sources appended

def test_solve_complex_query_no_action(reasoning_agent, mock_engine):
    mock_engine.generate.side_effect = [
        "THOUGHT: I know this.\nACTION: ANSWER", 
        "It is a show."
    ]
    ans = reasoning_agent.solve_complex_query("What is Anime?", "Anime")
    assert ans == "It is a show."

@pytest.mark.asyncio
async def test_on_bus_message(reasoning_agent):
    # Smoke test for callback
    from unittest.mock import AsyncMock
    mock_bus = MagicMock()
    mock_bus.read_shared_memory = AsyncMock()
    reasoning_agent.agent_bus = mock_bus
    await reasoning_agent._on_bus_message("msg1")
    mock_bus.read_shared_memory.assert_called_once_with("msg1")
