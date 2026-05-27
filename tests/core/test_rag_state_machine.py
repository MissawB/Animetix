import pytest
from unittest.mock import MagicMock, patch
from core.domain.services.agentic_rag_service import AgenticRAGService, RAGState, RAGContext
from core.domain.entities.ai_schemas import SearchPlan, JudgeEvaluation, JudgeAction, StreamStep, DebateOutcome

@pytest.fixture
def mock_deps():
    mock_xai = MagicMock()
    mock_xai.measure_confidence.return_value = 1.0
    mock_pm = MagicMock()
    mock_pm.get_prompt.return_value = ("prompt", "system")
    
    mock_rag = MagicMock()
    mock_router = MagicMock()
    mock_router.classify.return_value = "COMPLEX"

    from core.domain.services.rag_workflow_manager import RAGWorkflowManager
    mock_wm = RAGWorkflowManager(
        planner=MagicMock(),
        critic=MagicMock(),
        synthesizer=MagicMock(),
        judge=MagicMock(),
        scout=MagicMock(),
        semantic_router=mock_router,
        retrieval_evaluator=MagicMock(),
        community_partitioner=MagicMock(),
        graph_expert=MagicMock(),
        debate_manager=MagicMock(),
        librarian=MagicMock(),
        forge=MagicMock(),
        saga_agent=MagicMock(),
        chronicler=MagicMock(),
        uncertainty_service=mock_xai,
        inference_engine=MagicMock(),
        web_search=MagicMock(),
        prompt_manager=mock_pm,
        rag_service=mock_rag,
    )
    return {
        'inference_engine': MagicMock(),
        'rag_service': mock_rag,
        'web_search': MagicMock(),
        'prompt_manager': mock_pm,
        'llm_service': MagicMock(),
        'workflow_manager': mock_wm,
        'obs_service': MagicMock(),
        'uncertainty_service': mock_xai,
        'semantic_router': mock_router
    }

def test_research_more_loop_integration(mock_deps):
    service = AgenticRAGService(**mock_deps)
    service.planner = MagicMock()
    service.scout = MagicMock()
    service.synthesizer = MagicMock()
    service.librarian = MagicMock()
    service.librarian.identify_gaps.return_value = []
    
    service._assess_complexity = MagicMock(return_value=(0, 0))
    service._get_memories = MagicMock(return_value="")
    service._execute_search = MagicMock(return_value=([], "raw_results"))
    
    service.planner.plan.return_value = SearchPlan(optimized_query="test query", requires_web=False, reasoning="test")
    service.scout.find_truth_path.return_value = "truth_path"
    service.synthesizer.synthesize_stream.return_value = iter(["Réponse", " finale"])
    
    outcome1 = DebateOutcome(consensus_action=JudgeAction.RESEARCH_MORE, final_reasoning="Need info", critiques={})
    outcome2 = DebateOutcome(consensus_action=JudgeAction.APPROVE, final_reasoning="ok", critiques={})
    service.debate_manager.conduct_debate = MagicMock(side_effect=[outcome1, outcome2])
    
    with patch('core.domain.services.agentic_rag_service.RAGContext') as MockContext:
        def side_effect_ctx(**kwargs):
            kwargs['max_iterations'] = 10
            return RAGContext(**kwargs)
        MockContext.side_effect = side_effect_ctx
        events = list(service.plan_and_solve_stream("Query", "Anime"))
    
    state_logs = [e['content'] for e in events if e['type'] == 'thought' and "[State Machine]" in e['content']]
    
    # Sequence should contain these states in order
    states = [s for s in state_logs]
    assert any("PLAN" in s for s in states)
    assert any("RESEARCH" in s for s in states)
    assert any("SYNTHESIZE" in s for s in states)
    assert any("JUDGE" in s for s in states)

def test_rewrite_loop(mock_deps):
    service = AgenticRAGService(**mock_deps)
    service.planner = MagicMock()
    service.scout = MagicMock()
    service.synthesizer = MagicMock()
    service.librarian = MagicMock()
    service.librarian.identify_gaps.return_value = []
    
    service._assess_complexity = MagicMock(return_value=(0, 0))
    service._execute_search = MagicMock(return_value=([], "raw"))
    service._get_memories = MagicMock(return_value="")

    service.planner.plan.return_value = SearchPlan(optimized_query="test", requires_web=False, reasoning="test")
    service.scout.find_truth_path.return_value = "truth"
    service.synthesizer.synthesize_stream.return_value = iter(["Fix"])
    
    outcome1 = DebateOutcome(consensus_action=JudgeAction.REWRITE, final_reasoning="Fix style", critiques={})
    outcome2 = DebateOutcome(consensus_action=JudgeAction.APPROVE, final_reasoning="ok", critiques={})
    service.debate_manager.conduct_debate = MagicMock(side_effect=[outcome1, outcome2])
    
    events = list(service.plan_and_solve_stream("query", "Anime"))
    state_logs = [e['content'] for e in events if e['type'] == 'thought' and "[State Machine]" in e['content']]
    
    assert len(state_logs) > 0
    assert any("SYNTHESIZE" in s for s in state_logs)
    assert any("JUDGE" in s for s in state_logs)
