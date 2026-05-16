import pytest
from unittest.mock import MagicMock
from core.domain.services.agentic_rag_service import AgenticRAGService

@pytest.fixture
def mock_engine():
    engine = MagicMock()
    # For stream_generate
    engine.stream_generate.return_value = iter(["The ", "answer."])
    return engine

@pytest.fixture
def mock_rag():
    rag = MagicMock()
    # On met une description longue pour déclencher le Scout
    rag.hybrid_search.return_value = [{'title': 'DB Result', 'id': '1', 'description': 'A' * 600}]
    return rag

@pytest.fixture
def mock_web():
    web = MagicMock()
    web.search.return_value = [{'title': 'Web Result', 'snippet': 'W' * 600}]
    return web

@pytest.fixture
def mock_prompt_manager():
    pm = MagicMock()
    pm.get_prompt.return_value = ("prompt", "system")
    return pm

@pytest.fixture
def agentic_rag(mock_engine, mock_rag, mock_web, mock_prompt_manager):
    return AgenticRAGService(inference_engine=mock_engine, rag_service=mock_rag, web_search=mock_web, prompt_manager=mock_prompt_manager)

def test_plan_and_solve_local_path(agentic_rag, mock_engine, mock_rag):
    mock_engine.generate.side_effect = [
        '{"complexity_score": 0, "thinking_budget": 0}', # 0. TTC
        '{"optimized_query": "Naruto facts", "requires_web": false, "reasoning": "R"}', # 1. Planner
        "Truth Path from Scout", # 2. Scout
        '{"is_relevant": true, "relevance_score": 1.0, "suggested_action": "PROCEED"}', # 3. Critic
        '{"is_reliable": true, "faithfulness_score": 1.0, "relevancy_score": 1.0, "hallucination_detected": false, "reasoning": "ok"}' # 4. Judge
    ]
    
    res = agentic_rag.plan_and_solve("Who is Naruto?", "Anime")
    assert "The answer." in res
    mock_rag.hybrid_search.assert_called_once()

def test_plan_and_solve_web_path(agentic_rag, mock_engine, mock_web):
    mock_engine.generate.side_effect = [
        '{"complexity_score": 0, "thinking_budget": 0}', # 0. TTC
        '{"optimized_query": "Latest news", "requires_web": true, "reasoning": "R"}', # 1. Planner
        "Web Truth Path", # 2. Scout
        '{"is_relevant": true, "relevance_score": 1.0, "suggested_action": "PROCEED"}', # 3. Critic
        '{"is_reliable": true, "faithfulness_score": 1.0, "relevancy_score": 1.0, "hallucination_detected": false, "reasoning": "ok"}' # 4. Judge
    ]
    
    res = agentic_rag.plan_and_solve("News?", "Anime")
    assert "the answer." in res.lower()
    mock_web.search.assert_called_once()

def test_plan_and_solve_with_reformulation(agentic_rag, mock_engine, mock_rag, mock_web):
    mock_engine.generate.side_effect = [
        '{"complexity_score": 0, "thinking_budget": 0}', # 0. TTC
        '{"optimized_query": "Naruto year", "requires_web": false, "reasoning": "R"}', # 1. Planner
        "Initial Truth Path", # 2. Scout 1
        '{"is_relevant": false, "relevance_score": 0.2, "suggested_action": "TRIGGER_WEB"}', # 3. Critic 1 (Fail)
        "Web Truth Path", # 4. Scout 2 (after web)
        '{"is_relevant": true, "relevance_score": 1.0, "suggested_action": "PROCEED"}', # 5. Critic 2 (Success)
        '{"is_reliable": true, "faithfulness_score": 1.0, "relevancy_score": 1.0, "hallucination_detected": false, "reasoning": "ok"}' # 6. Judge
    ]
    
    res = agentic_rag.plan_and_solve("When did Naruto start?", "Anime")
    assert "answer" in res
    assert mock_rag.hybrid_search.call_count == 1
    assert mock_web.search.call_count == 1

from unittest.mock import MagicMock, patch

def test_extract_json_logs_error_on_invalid_json(agentic_rag):
    invalid_json_text = "Here is some text with { invalid json }"
    
    with patch("core.domain.services.agentic_rag_service.logger") as mock_logger:
        res = agentic_rag._extract_json(invalid_json_text)
        assert res == {}
        mock_logger.error.assert_called()
        args, _ = mock_logger.error.call_args
        assert "Failed to parse JSON" in args[0]

