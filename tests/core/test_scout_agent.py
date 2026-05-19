import pytest
from unittest.mock import MagicMock
from core.domain.services.rag.agents.scout import ScoutAgent

@pytest.fixture
def mock_llm():
    return MagicMock()

@pytest.fixture
def mock_pm():
    pm = MagicMock()
    pm.get_prompt.return_value = ("scout prompt", "scout system")
    return pm

def test_scout_agent_distill_success(mock_llm, mock_pm):
    agent = ScoutAgent(llm_service=mock_llm, prompt_manager=mock_pm)
    
    mock_llm.generate.return_value = "This is a condensed truth path with meaningful content and more than fifty characters."
    
    raw_context = "Essential context " * 100 # Long enough
    res = agent.find_truth_path("Query", None, raw_context)
    
    assert "meaningful content" in res
    mock_llm.generate.assert_called_once()

def test_scout_agent_fallback_on_short_response(mock_llm, mock_pm):
    agent = ScoutAgent(llm_service=mock_llm, prompt_manager=mock_pm)
    
    # Short response triggers fallback
    mock_llm.generate.return_value = "Too short."
    
    raw_context = "A" * 3000
    res = agent.find_truth_path("Query", None, raw_context)
    
    # Should return first 2000 chars of raw context as fallback
    assert len(res) == 2000
    assert res == raw_context[:2000]

def test_scout_agent_fallback_on_empty_response(mock_llm, mock_pm):
    agent = ScoutAgent(llm_service=mock_llm, prompt_manager=mock_pm)
    
    mock_llm.generate.return_value = ""
    
    res = agent.find_truth_path("Query", None, "Some context")
    assert res == "Some context"[:2000]
