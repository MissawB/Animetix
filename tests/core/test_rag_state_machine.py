import pytest
from unittest.mock import MagicMock, patch
from core.domain.services.agentic_rag_service import AgenticRAGService, RAGState, RAGContext
from core.domain.entities.ai_schemas import SearchPlan, JudgeEvaluation, JudgeAction, StreamStep, DebateOutcome
from core.domain.services.rag_orchestrator import RAGOrchestrator
from core.domain.services.rag.processors.plan_processor import PlanProcessor
from core.domain.services.rag.processors.research_processor import ResearchProcessor
from core.domain.services.rag.processors.synthesize_processor import SynthesizeProcessor
from core.domain.services.rag.processors.judge_processor import JudgeProcessor
from core.domain.services.rag.processors.acquire_knowledge_processor import AcquireKnowledgeProcessor
from core.domain.services.rag.processors.speculate_processor import SpeculateProcessor
from core.domain.services.rag.processors.vlm_rerank_processor import VlmRerankProcessor
from core.domain.services.rag.processors.saga_lookup_processor import SagaLookupProcessor
from core.domain.services.rag.processors.graph_explore_processor import GraphExploreProcessor
from core.domain.services.rag.processors.fallback_rag_processor import FallbackRagProcessor


@pytest.fixture
def mock_deps():
    mock_xai = MagicMock()
    mock_xai.measure_confidence.return_value = 1.0
    mock_pm = MagicMock()
    mock_pm.get_prompt.return_value = ("prompt", "system")
    
    mock_rag = MagicMock()
    mock_router = MagicMock()
    mock_router.classify.return_value = "COMPLEX"

    mock_planner = MagicMock()
    mock_scout = MagicMock()
    mock_synthesizer = MagicMock()
    mock_judge = MagicMock()
    mock_librarian = MagicMock()
    mock_forge = MagicMock()
    mock_saga_agent = MagicMock()
    mock_graph_expert = MagicMock()
    mock_debate_manager = MagicMock()

    # Mock the 'process' method of each processor to act as a generator
    def mock_generator_factory(state_name, next_state):
        def _generator_func(*args, **kwargs):
            yield StreamStep(type="thought", content=f"[State Machine] {state_name}")
            return next_state
        return _generator_func

    mock_processors = {
        RAGState.PLAN: MagicMock(spec=PlanProcessor, planner=mock_planner),
        RAGState.RESEARCH: MagicMock(spec=ResearchProcessor, planner=mock_planner, web_search=MagicMock(), retrieval_evaluator=MagicMock(), context_compressor=MagicMock(), scout=mock_scout, video_rag_service=MagicMock(), neo4j_manager=MagicMock(), rag_service=mock_rag),
        RAGState.SYNTHESIZE: MagicMock(spec=SynthesizeProcessor, synthesizer=mock_synthesizer, xai_service=mock_xai, rag_service=mock_rag),
        RAGState.JUDGE: MagicMock(spec=JudgeProcessor, debate_manager=mock_debate_manager),
        RAGState.ACQUIRE_KNOWLEDGE: MagicMock(spec=AcquireKnowledgeProcessor, librarian=mock_librarian),
        RAGState.SPECULATE: MagicMock(spec=SpeculateProcessor, forge=mock_forge),
        RAGState.VLM_RERANK: MagicMock(spec=VlmRerankProcessor, prompt_manager=mock_pm, inference_engine=MagicMock()),
        RAGState.SAGA_LOOKUP: MagicMock(spec=SagaLookupProcessor, saga_agent=mock_saga_agent),
        RAGState.GRAPH_EXPLORE: MagicMock(spec=GraphExploreProcessor, community_partitioner=MagicMock(), graph_expert=mock_graph_expert, neo4j_manager=MagicMock()),
        RAGState.FALLBACK_RAG: MagicMock(spec=FallbackRagProcessor, rag_service=mock_rag, inference_engine=MagicMock(), expert_facts=[]),
    }

    mock_processors[RAGState.PLAN].process.side_effect = mock_generator_factory(RAGState.PLAN.name, RAGState.RESEARCH)
    mock_processors[RAGState.RESEARCH].process.side_effect = mock_generator_factory(RAGState.RESEARCH.name, RAGState.SYNTHESIZE)
    mock_processors[RAGState.SYNTHESIZE].process.side_effect = mock_generator_factory(RAGState.SYNTHESIZE.name, RAGState.JUDGE)
    mock_processors[RAGState.JUDGE].process.side_effect = mock_generator_factory(RAGState.JUDGE.name, RAGState.FINALIZE)
    # Configure specific side effects for judge_processor based on test scenarios
    # These will be overridden in the test functions as needed

    mock_orchestrator = RAGOrchestrator(processors=mock_processors)

    return {
        'inference_engine': MagicMock(),
        'rag_service': mock_rag,
        'web_search': MagicMock(),
        'prompt_manager': mock_pm,
        'llm_service': MagicMock(),
        'workflow_orchestrator': mock_orchestrator, # Updated
        'obs_service': MagicMock(),
        'xai_service': mock_xai,
        'semantic_router': mock_router
    }

def test_research_more_loop_integration(mock_deps):
    service = AgenticRAGService(**mock_deps)
    
    outcome1 = DebateOutcome(consensus_action=JudgeAction.RESEARCH_MORE, final_reasoning="Need info", critiques={})
    outcome2 = DebateOutcome(consensus_action=JudgeAction.APPROVE, final_reasoning="ok", critiques={})
    mock_deps['workflow_orchestrator'].processors[RAGState.JUDGE].debate_manager.conduct_debate.side_effect = [outcome1, outcome2]

    def judge_process_side_effect(ctx):
        yield StreamStep(type="thought", content=f"[State Machine] {RAGState.JUDGE.name}")
        if mock_deps['workflow_orchestrator'].processors[RAGState.JUDGE].debate_manager.conduct_debate.call_count == 1:
            return RAGState.RESEARCH
        else:
            return RAGState.FINALIZE
    mock_deps['workflow_orchestrator'].processors[RAGState.JUDGE].process.side_effect = judge_process_side_effect
    
    with patch('core.domain.services.agentic_rag_service.RAGContext') as MockContext:
        def side_effect_ctx(**kwargs):
            kwargs['max_iterations'] = 10
            return RAGContext(**kwargs)
        MockContext.side_effect = side_effect_ctx
        
        events = list(service.plan_and_solve_stream("Query", "Anime"))
    
    state_logs = [e.type for e in events if e.type == 'thought' and "State Machine" in e.content]
    
    assert RAGState.PLAN.name in state_logs[0]
    assert RAGState.RESEARCH.name in state_logs[1]
    assert RAGState.SYNTHESIZE.name in state_logs[2]
    assert RAGState.JUDGE.name in state_logs[3]
    assert RAGState.RESEARCH.name in state_logs[4] # RESEARCH_MORE loop
    assert RAGState.SYNTHESIZE.name in state_logs[5]
    assert RAGState.JUDGE.name in state_logs[6]
    
    # Check that plan, research, synthesize, judge processors were called
    service.orchestrator.processors[RAGState.PLAN].process.assert_called()
    service.orchestrator.processors[RAGState.RESEARCH].process.assert_called()
    service.orchestrator.processors[RAGState.SYNTHESIZE].process.assert_called()
    service.orchestrator.processors[RAGState.JUDGE].process.assert_called()

def test_rewrite_loop(mock_deps):
    service = AgenticRAGService(**mock_deps)
    
    outcome1 = DebateOutcome(consensus_action=JudgeAction.REWRITE, final_reasoning="Fix style", critiques={})
    outcome2 = DebateOutcome(consensus_action=JudgeAction.APPROVE, final_reasoning="ok", critiques={})
    mock_deps['workflow_orchestrator'].processors[RAGState.JUDGE].debate_manager.conduct_debate.side_effect = [outcome1, outcome2]

    def judge_process_side_effect(ctx):
        yield StreamStep(type="thought", content=f"[State Machine] {RAGState.JUDGE.name}")
        if mock_deps['workflow_orchestrator'].processors[RAGState.JUDGE].debate_manager.conduct_debate.call_count == 1:
            return RAGState.SYNTHESIZE
        else:
            return RAGState.FINALIZE
    mock_deps['workflow_orchestrator'].processors[RAGState.JUDGE].process.side_effect = judge_process_side_effect

    events = list(service.plan_and_solve_stream("query", "Anime"))
    state_logs = [e.type for e in events if e.type == 'thought' and "State Machine" in e.content]
    
    assert RAGState.PLAN.name in state_logs[0]
    assert RAGState.RESEARCH.name in state_logs[1]
    assert RAGState.SYNTHESIZE.name in state_logs[2]
    assert RAGState.JUDGE.name in state_logs[3]
    assert RAGState.SYNTHESIZE.name in state_logs[4] # REWRITE loop
    assert RAGState.JUDGE.name in state_logs[5]

    # Check that plan, research, synthesize, judge processors were called
    service.orchestrator.processors[RAGState.PLAN].process.assert_called()
    service.orchestrator.processors[RAGState.RESEARCH].process.assert_called()
    service.orchestrator.processors[RAGState.SYNTHESIZE].process.assert_called()
    service.orchestrator.processors[RAGState.JUDGE].process.assert_called()