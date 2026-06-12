import pytest
from unittest.mock import MagicMock, patch
from backend.core.domain.entities.ai_schemas import RAGContext, RAGState, StreamStep, JudgeAction, SearchPlan, DebateOutcome
from backend.core.domain.exceptions import InfrastructureError, InferenceError

from backend.core.domain.services.rag.processors.saga_lookup_processor import SagaLookupProcessor
from backend.core.domain.services.rag.processors.graph_explore_processor import GraphExploreProcessor
from backend.core.domain.services.rag.processors.research_processor import ResearchProcessor
from backend.core.domain.services.rag.processors.synthesize_processor import SynthesizeProcessor
from backend.core.domain.services.rag.processors.judge_processor import JudgeProcessor
from backend.core.domain.services.rag.processors.fallback_rag_processor import FallbackRagProcessor
from backend.core.domain.services.rag.processors.vlm_rerank_processor import VlmRerankProcessor
from backend.core.domain.services.rag.processors.acquire_knowledge_processor import AcquireKnowledgeProcessor

def consume_generator(gen):
    steps = []
    try:
        while True:
            steps.append(next(gen))
    except StopIteration as e:
        return e.value, steps

# 1. SagaLookupProcessor Tests
def test_saga_lookup_processor_success():
    mock_saga_agent = MagicMock()
    mock_saga_agent.lookup_saga.return_value = "One Piece"
    mock_saga_agent.get_saga_context.return_value = "One Piece global summary"
    
    processor = SagaLookupProcessor(mock_saga_agent)
    ctx = MagicMock(spec=RAGContext)
    ctx.query = "Who is Luffy?"
    ctx.truth_path = "initial text"
    ctx.plan = MagicMock(spec=SearchPlan)
    ctx.plan.requires_graph = False
    
    next_state, steps = consume_generator(processor.process(ctx))
    
    assert next_state == RAGState.RESEARCH
    assert ctx.saga_name == "One Piece"
    assert "### RÉSUMÉ GLOBAL DE LA SAGA (One Piece) ###" in ctx.truth_path
    assert "One Piece global summary" in ctx.truth_path
    mock_saga_agent.lookup_saga.assert_called_once_with(ctx.query)
    mock_saga_agent.get_saga_context.assert_called_once_with("One Piece")

def test_saga_lookup_processor_transitions_to_graph():
    mock_saga_agent = MagicMock()
    mock_saga_agent.lookup_saga.return_value = None
    
    processor = SagaLookupProcessor(mock_saga_agent)
    ctx = MagicMock(spec=RAGContext)
    ctx.query = "Who is Luffy?"
    ctx.plan = MagicMock(spec=SearchPlan)
    ctx.plan.requires_graph = True
    
    next_state, _ = consume_generator(processor.process(ctx))
    assert next_state == RAGState.GRAPH_EXPLORE

# 2. GraphExploreProcessor Tests
def test_graph_explore_processor_no_plan():
    processor = GraphExploreProcessor(None, None, None)
    ctx = MagicMock(spec=RAGContext)
    ctx.plan = None
    
    next_state, _ = consume_generator(processor.process(ctx))
    assert next_state == RAGState.PLAN

def test_graph_explore_processor_success():
    mock_partitioner = MagicMock()
    mock_partitioner.search_communities.return_value = [
        {"name": "Studio Ghibli", "summary": "Ghibli community", "entities": ["Miyazaki", "Totoro"]}
    ]
    mock_expert = MagicMock()
    mock_expert.generate_cypher.return_value = "MATCH (n) RETURN n"
    
    mock_neo4j = MagicMock()
    mock_neo4j.execute_read.return_value = "Neo4j Cypher Output"
    
    processor = GraphExploreProcessor(mock_partitioner, mock_expert, mock_neo4j)
    ctx = MagicMock(spec=RAGContext)
    ctx.query = "test"
    ctx.truth_path = ""
    ctx.plan = MagicMock(spec=SearchPlan)
    ctx.plan.reasoning = "test reasoning"
    
    next_state, _ = consume_generator(processor.process(ctx))
    
    assert next_state == RAGState.RESEARCH
    assert "### CONTEXTE GRAPHRAG (COMMUNAUTÉS THÉMATIQUES) ###" in ctx.truth_path
    assert "Studio Ghibli" in ctx.truth_path
    assert "Neo4j Cypher Output" in ctx.truth_path
    mock_partitioner.search_communities.assert_called_once()
    mock_expert.generate_cypher.assert_called_once()
    mock_neo4j.execute_read.assert_called_once_with("MATCH (n) RETURN n")

# 3. ResearchProcessor Tests
def test_research_processor_no_plan():
    processor = ResearchProcessor(None, None, None, None, None, None, None, None)
    ctx = MagicMock(spec=RAGContext)
    ctx.plan = None
    
    next_state, _ = consume_generator(processor.process(ctx))
    assert next_state == RAGState.PLAN

def test_research_processor_web_search():
    mock_planner = MagicMock()
    mock_web_search = MagicMock()
    mock_web_search.search.return_value = [
        {"title": "Web Title", "snippet": "Web content snippet", "url": "http://test.com"}
    ]
    mock_scout = MagicMock()
    mock_scout.find_truth_path.return_value = "Distilled Truth Path"
    
    processor = ResearchProcessor(
        planner=mock_planner,
        rag_service=MagicMock(),
        context_compressor=MagicMock(),
        retrieval_evaluator=MagicMock(),
        web_search=mock_web_search,
        video_rag_service=MagicMock(),
        scout=mock_scout,
        neo4j_manager=None
    )
    
    ctx = MagicMock(spec=RAGContext)
    ctx.query = "Search query"
    ctx.truth_path = ""
    ctx.media_type = "Anime"
    ctx.plan = MagicMock(spec=SearchPlan)
    ctx.plan.requires_web = True
    ctx.plan.is_visual_query = False
    ctx.plan.optimized_query = "optimized query"
    ctx.plan.entities = []
    
    next_state, _ = consume_generator(processor.process(ctx))
    
    assert next_state == RAGState.SYNTHESIZE
    assert ctx.candidates == [{"title": "Web Title", "description": "Web content snippet", "image_url": "http://test.com"}]
    assert "Distilled Truth Path" in ctx.truth_path
    mock_web_search.search.assert_called_once_with("optimized query")

# 4. SynthesizeProcessor Tests
def test_synthesize_processor_success():
    mock_synth = MagicMock()
    mock_synth.synthesize_stream.return_value = ["<thought>", "think", "</thought>", "Final", " ", "Answer"]
    mock_xai = MagicMock()
    mock_xai.measure_confidence.return_value = {"confidence_score": 0.9}
    
    processor = SynthesizeProcessor(mock_synth, mock_xai, MagicMock())
    ctx = MagicMock(spec=RAGContext)
    ctx.query = "query"
    ctx.truth_path = "truth"
    ctx.thinking_budget = 100
    ctx.thinking_mode = "fast"
    ctx.correction_feedback = None
    ctx.knowledge_acquired = False
    
    next_state, steps = consume_generator(processor.process(ctx))
    
    assert next_state == RAGState.JUDGE
    assert ctx.full_answer == "Final Answer"
    # Verify thoughts were yielded
    thought_steps = [s for s in steps if s.get("type") == "thought"]
    assert any("think" in s.get("content") for s in thought_steps)

# 5. JudgeProcessor Tests
def test_judge_processor_approve():
    mock_debate = MagicMock()
    outcome = DebateOutcome(consensus_action=JudgeAction.APPROVE, final_reasoning="looks good", critiques={})
    mock_debate.conduct_debate.return_value = outcome
    
    processor = JudgeProcessor(mock_debate)
    ctx = MagicMock(spec=RAGContext)
    ctx.query = "query"
    ctx.truth_path = "truth"
    ctx.full_answer = "answer"
    ctx.thinking_budget = 100
    ctx.thinking_mode = "fast"
    ctx.iteration = 1
    
    next_state, _ = consume_generator(processor.process(ctx))
    
    assert next_state == RAGState.FINALIZE
    assert ctx.debate_outcome == outcome

# 6. FallbackRagProcessor Tests
def test_fallback_rag_processor():
    mock_rag = MagicMock()
    mock_rag.hybrid_search.return_value = [
        {"title": "Fallback Title", "description": "Fallback Description"}
    ]
    mock_inference = MagicMock()
    mock_inference.stream_generate.return_value = ["Fallback", " ", "Result"]
    
    processor = FallbackRagProcessor(mock_rag, mock_inference, [{"primary_keywords": ["test"], "fact": "Rule Fact"}])
    ctx = MagicMock(spec=RAGContext)
    ctx.query = "test query"
    ctx.media_type = "Anime"
    
    next_state, steps = consume_generator(processor.process(ctx))
    
    assert next_state == RAGState.FINALIZE
    assert ctx.full_answer == "Fallback Result"
    mock_rag.hybrid_search.assert_called_once_with("test query", "Anime")
    mock_inference.stream_generate.assert_called_once()

# 7. VlmRerankProcessor Tests
def test_vlm_rerank_processor_no_images():
    processor = VlmRerankProcessor(MagicMock(), MagicMock())
    ctx = MagicMock(spec=RAGContext)
    ctx.candidates = [{"title": "No Image candidate"}]
    
    next_state, _ = consume_generator(processor.process(ctx))
    assert next_state == RAGState.SYNTHESIZE

def test_vlm_rerank_processor_success():
    mock_pm = MagicMock()
    mock_pm.get_prompt.return_value = ("prompt text", "system prompt")
    mock_inference = MagicMock()
    mock_inference.visual_rerank.return_value = [{"index": 0, "score": 0.85}]
    
    processor = VlmRerankProcessor(mock_pm, mock_inference)
    ctx = MagicMock(spec=RAGContext)
    ctx.query = "query"
    ctx.truth_path = ""
    ctx.candidates = [{"title": "Candidate 1", "image": "http://img.com/1"}]
    
    next_state, _ = consume_generator(processor.process(ctx))
    
    assert next_state == RAGState.SYNTHESIZE
    assert "Candidate 1 (Score Visuel: 0.85)" in ctx.truth_path

# 8. AcquireKnowledgeProcessor Tests
def test_acquire_knowledge_processor_gap_found():
    mock_librarian = MagicMock()
    mock_librarian.identify_gap.return_value = {"query": "Gap Query", "source_type": "web"}
    mock_librarian.fetch_data.return_value = "Fresh Gap Knowledge"
    
    processor = AcquireKnowledgeProcessor(mock_librarian)
    ctx = MagicMock(spec=RAGContext)
    ctx.query = "query"
    ctx.truth_path = ""
    
    next_state, _ = consume_generator(processor.process(ctx))
    
    assert next_state == RAGState.SYNTHESIZE
    assert ctx.knowledge_acquired is True
    assert "Fresh Gap Knowledge" in ctx.truth_path

# 9. Bilingual / Language Tests
def test_rag_context_language():
    from backend.core.domain.entities.ai_schemas import RAGContext
    ctx = RAGContext(query="test", media_type="Anime")
    assert ctx.language == "Français"
    
    ctx_en = RAGContext(query="test", media_type="Anime", language="English")
    assert ctx_en.language == "English"

def test_agentic_rag_service_propagates_language(monkeypatch):
    from backend.core.domain.services.agentic_rag_service import AgenticRAGService
    from unittest.mock import MagicMock
    
    # Mock dependencies
    mock_engine = MagicMock()
    mock_rag = MagicMock()
    mock_search = MagicMock()
    mock_prompt = MagicMock()
    mock_llm = MagicMock()
    mock_orch = MagicMock()
    
    service = AgenticRAGService(
        inference_engine=mock_engine,
        rag_service=mock_rag,
        web_search=mock_search,
        prompt_manager=mock_prompt,
        llm_service=mock_llm,
        workflow_orchestrator=mock_orch
    )
    
    # Mock semantic router to trigger standard flow
    service.semantic_router.classify = MagicMock(return_value="COMPLEX")
    service._assess_complexity = MagicMock(return_value=(1000, 2))
    service._check_cache = MagicMock(return_value=None)
    service._get_memories = MagicMock(return_value="")
    
    # Intercept run_workflow to verify context language
    def mock_run_workflow(ctx, xai_collector=None):
        assert ctx.language == "English"
        yield from []
    mock_orch.run_workflow.side_effect = mock_run_workflow
    
    # Run stream
    list(service.plan_and_solve_stream("Who is Naruto?", "Anime", language="English"))

def test_response_synthesizer_respects_language():
    from backend.core.domain.services.rag.agents.synthesizer import ResponseSynthesizer
    from unittest.mock import MagicMock
    
    mock_engine = MagicMock()
    mock_prompt_mgr = MagicMock()
    mock_prompt_mgr.get_prompt.return_value = ("formatted_prompt", "system_prompt")
    
    synthesizer = ResponseSynthesizer(mock_engine, mock_prompt_mgr)
    list(synthesizer.synthesize_stream("query", "context", language="English"))
    
    mock_prompt_mgr.get_prompt.assert_called_with(
        "synthesizer_final", query="query", context="context", feedback=None, language="English"
    )

def test_fallback_processor_english():
    from backend.core.domain.services.rag.processors.fallback_rag_processor import FallbackRagProcessor
    from backend.core.domain.entities.ai_schemas import RAGContext, RAGState
    from unittest.mock import MagicMock
    
    mock_rag = MagicMock()
    mock_rag.hybrid_search.return_value = [{"title": "Title", "description": "Desc"}]
    mock_engine = MagicMock()
    mock_engine.stream_generate.return_value = ["Answer"]
    
    processor = FallbackRagProcessor(mock_rag, mock_engine, [])
    ctx = RAGContext(query="What is Naruto?", media_type="Anime", language="English")
    
    states = list(processor.process(ctx))
    
    mock_engine.stream_generate.assert_called_once()
    args = mock_engine.stream_generate.call_args[0]
    assert "Answer the following question" in args[0]
    assert "You are an expert assistant" in args[1]


