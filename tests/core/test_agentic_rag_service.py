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
    mock_xai = MagicMock()
    mock_xai.measure_confidence.return_value = 0.95
    return AgenticRAGService(inference_engine=mock_engine, rag_service=mock_rag, web_search=mock_web, prompt_manager=mock_prompt_manager, uncertainty_service=mock_xai)

def test_plan_and_solve_local_path(agentic_rag, mock_engine, mock_rag):
    mock_engine.generate.side_effect = [
        '{"complexity_score": 0, "thinking_budget": 0}', # 0. TTC
        '{"optimized_query": "Naruto facts", "requires_web": false, "reasoning": "R"}', # 1. Planner
        "Truth Path from Scout", # 2. Scout
        '{"is_reliable": true, "faithfulness_score": 1.0, "relevancy_score": 1.0, "hallucination_detected": false, "reasoning": "ok", "next_action": "APPROVE"}' # 3. Judge
    ]
    
    res = agent_rag_plan_and_solve(agentic_rag, "Who is Naruto?", "Anime")
    assert "answer." in res["answer"]
    mock_rag.hybrid_search.assert_called_once()

def test_plan_and_solve_web_path(agentic_rag, mock_engine, mock_web):
    mock_engine.generate.side_effect = [
        '{"complexity_score": 0, "thinking_budget": 0}', # 0. TTC
        '{"optimized_query": "Latest news", "requires_web": true, "reasoning": "R"}', # 1. Planner
        "Web Truth Path", # 2. Scout
        '{"is_reliable": true, "faithfulness_score": 1.0, "relevancy_score": 1.0, "hallucination_detected": false, "reasoning": "ok", "next_action": "APPROVE"}' # 3. Judge
    ]
    
    res = agent_rag_plan_and_solve(agentic_rag, "News?", "Anime")
    assert "answer." in res["answer"].lower()
    mock_web.search.assert_called_once()

def test_plan_and_solve_with_reformulation(agentic_rag, mock_engine, mock_rag, mock_web):
    from core.domain.entities.ai_schemas import SearchPlan, DebateOutcome, JudgeAction
    
    plan1 = SearchPlan(optimized_query="Naruto year", requires_web=False, reasoning="R")
    plan2 = SearchPlan(optimized_query="Naruto debut year", requires_web=True, reasoning="Need web")
    
    # Premier débat: on demande un Re-plan
    outcome1 = DebateOutcome(consensus_action=JudgeAction.REPLAN, final_reasoning="Need web info", critiques={})
    # Deuxième débat: on approuve
    outcome2 = DebateOutcome(consensus_action=JudgeAction.APPROVE, final_reasoning="ok", critiques={})

    # Force high confidence to skip Librarian
    agentic_rag.uncertainty_service.measure_confidence.return_value = 1.0

    with patch.object(agentic_rag.planner, 'plan', side_effect=[plan1, plan2]), \
         patch.object(agentic_rag.scout, 'find_truth_path', return_value="Truth Path"), \
         patch.object(agentic_rag.debate_manager, 'conduct_debate', side_effect=[outcome1, outcome2]), \
         patch.object(agentic_rag, '_assess_complexity', return_value=(0, 0)):
        
        res = agent_rag_plan_and_solve(agentic_rag, "When did Naruto start?", "Anime")
        assert "answer" in res
        assert mock_web.search.called

def test_vlm_rerank_path(agentic_rag, mock_engine, mock_rag):
    mock_engine.generate.side_effect = [
        '{"complexity_score": 2, "thinking_budget": 100}', # 0. TTC
        '{"optimized_query": "visual query", "requires_web": false, "is_visual_query": true, "reasoning": "visual search"}', # 1. Planner
        "Truth Path from Scout", # 2. Scout
        '{"is_reliable": true, "faithfulness_score": 1.0, "relevancy_score": 1.0, "hallucination_detected": false, "reasoning": "ok", "next_action": "APPROVE"}' # 3. Judge
    ]
    mock_rag.hybrid_search.return_value = [{'title': 'DB Result', 'id': '1', 'description': 'A' * 600, 'image_url': 'http://image.jpg'}]
    mock_engine.visual_rerank.return_value = [
        {'index': 0, 'score': 0.9}
    ]
    
    # Run the stream and collect states
    states = []
    for step in agentic_rag.plan_and_solve_stream("Visual query", "Anime"):
        if step['type'] == 'thought' and "[State Machine]" in step['content']:
            states.append(step['content'])
            
    assert any("État: RAGState.VLM_RERANK" in s for s in states)
    mock_engine.visual_rerank.assert_called_once()

def agent_rag_plan_and_solve(service, query, media):
    # Helper to consume the stream and return final dict
    res = {}
    for step in service.plan_and_solve_stream(query, media):
        if step['type'] == 'token':
            res['answer'] = res.get('answer', '') + step['content']
    return res

from unittest.mock import MagicMock, patch

def test_extract_json_logs_error_on_invalid_json(agentic_rag):
    invalid_json_text = "Here is some text with { invalid json }"
    
    with patch("core.domain.services.agentic_rag_service.logger") as mock_logger:
        res = agentic_rag._extract_json(invalid_json_text)
        assert res == {}
        mock_logger.error.assert_called()
        args, _ = mock_logger.error.call_args
        assert "Failed to parse JSON" in args[0]

