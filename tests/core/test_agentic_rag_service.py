from unittest.mock import MagicMock

import pytest
from core.domain.entities.ai_schemas import (
    DebateOutcome,
    InferenceResponse,
    JudgeAction,
    SearchPlan,
)

from tests.helpers.agentic_rag_factory import build_test_agentic_rag_service
from tests.helpers.async_stream import as_async_iter, collect_async

# Drives the full agentic RAG pipeline against a live inference engine (no ollama in CI).
pytestmark = pytest.mark.integration


@pytest.fixture
def mock_engine():
    engine = MagicMock()
    # For stream_generate
    engine.stream_generate.return_value = iter(["The ", "answer."])
    return engine


@pytest.fixture
def mock_rag():
    rag = MagicMock()
    rag.hybrid_search.return_value = [
        {"title": "DB Result", "id": "1", "description": "A" * 600}
    ]
    return rag


@pytest.fixture
def mock_web():
    web = MagicMock()
    web.search.return_value = [{"title": "Web Result", "snippet": "W" * 600}]
    return web


@pytest.fixture
def mock_prompt_manager():
    pm = MagicMock()
    pm.get_prompt.return_value = ("prompt", "system")
    return pm


@pytest.fixture
def agentic_rag(mock_engine, mock_rag, mock_web, mock_prompt_manager):
    mock_xai = MagicMock()
    mock_xai.measure_confidence.return_value = 1.0

    service = build_test_agentic_rag_service(
        inference_engine=mock_engine,
        rag_service=mock_rag,
        web_search=mock_web,
        prompt_manager=mock_prompt_manager,
        llm_service=MagicMock(),
        workflow_orchestrator=MagicMock(),  # Triggers real orchestrator construction
        uncertainty_service=mock_xai,
    )

    # Mock router to return COMPLEX by default for integration tests
    service.semantic_router.classify = MagicMock(return_value="COMPLEX")
    # Mock complexity analysis
    service._assess_complexity = MagicMock(return_value=(0, 1))

    # Mock all agents to avoid real LLM calls through them
    service.planner = MagicMock()
    service.scout = MagicMock()
    service.debate_manager = MagicMock()
    service.synthesizer = MagicMock()
    service.librarian = MagicMock()

    return service


def test_plan_and_solve_local_path(agentic_rag, mock_engine, mock_rag):
    plan = SearchPlan(optimized_query="Naruto facts", requires_web=False, reasoning="R")
    agentic_rag.planner.plan.return_value = plan
    agentic_rag.scout.find_truth_path.return_value = "Truth Path from Scout"

    outcome = DebateOutcome(
        consensus_action=JudgeAction.APPROVE, final_reasoning="ok", critiques={}
    )
    agentic_rag.debate_manager.conduct_debate.return_value = outcome

    # Synthesizer mock: yields InferenceResponse chunks (SynthesizeProcessor reads .text)
    agentic_rag.synthesizer.asynthesize_stream.side_effect = as_async_iter(
        [InferenceResponse(text="The "), InferenceResponse(text="answer.")]
    )

    res = agent_rag_plan_and_solve(agentic_rag, "Who is Naruto?", "Anime")
    assert "answer." in res.get("answer", "")
    mock_rag.hybrid_search.assert_called()


def test_plan_and_solve_web_path(agentic_rag, mock_engine, mock_web):
    plan = SearchPlan(optimized_query="Latest news", requires_web=True, reasoning="R")
    agentic_rag.planner.plan.return_value = plan
    agentic_rag.scout.find_truth_path.return_value = "Web Truth Path"

    outcome = DebateOutcome(
        consensus_action=JudgeAction.APPROVE, final_reasoning="ok", critiques={}
    )
    agentic_rag.debate_manager.conduct_debate.return_value = outcome

    agentic_rag.synthesizer.asynthesize_stream.side_effect = as_async_iter(
        [InferenceResponse(text="The "), InferenceResponse(text="answer.")]
    )

    res = agent_rag_plan_and_solve(agentic_rag, "News?", "Anime")
    assert "answer." in res.get("answer", "").lower()
    mock_web.search.assert_called()


def test_plan_and_solve_with_reformulation(
    agentic_rag, mock_engine, mock_rag, mock_web
):
    plan1 = SearchPlan(optimized_query="Naruto year", requires_web=False, reasoning="R")
    plan2 = SearchPlan(
        optimized_query="Naruto debut year", requires_web=True, reasoning="Need web"
    )
    agentic_rag.planner.plan.side_effect = [plan1, plan2]

    agentic_rag.scout.find_truth_path.return_value = "Truth Path"

    outcome1 = DebateOutcome(
        consensus_action=JudgeAction.REPLAN, final_reasoning="Need more", critiques={}
    )
    outcome2 = DebateOutcome(
        consensus_action=JudgeAction.APPROVE, final_reasoning="ok", critiques={}
    )
    agentic_rag.debate_manager.conduct_debate.side_effect = [outcome1, outcome2]

    agentic_rag.synthesizer.asynthesize_stream.side_effect = as_async_iter(
        [InferenceResponse(text="The "), InferenceResponse(text="answer.")]
    )

    res = agent_rag_plan_and_solve(agentic_rag, "When did Naruto start?", "Anime")
    assert "answer" in res


def test_vlm_rerank_path(agentic_rag, mock_engine, mock_rag):
    plan = SearchPlan(
        optimized_query="visual query",
        requires_web=False,
        is_visual_query=True,
        reasoning="visual search",
    )
    agentic_rag.planner.plan.return_value = plan
    agentic_rag.scout.find_truth_path.return_value = "Truth Path"

    outcome = DebateOutcome(
        consensus_action=JudgeAction.APPROVE, final_reasoning="ok", critiques={}
    )
    agentic_rag.debate_manager.conduct_debate.return_value = outcome

    agentic_rag.synthesizer.asynthesize_stream.side_effect = as_async_iter(
        [InferenceResponse(text="The "), InferenceResponse(text="answer.")]
    )

    mock_rag.hybrid_search.return_value = [
        {
            "title": "DB Result",
            "id": "1",
            "description": "A" * 600,
            "image_url": "http://image.jpg",
        }
    ]
    mock_engine.visual_rerank.return_value = [{"index": 0, "score": 0.9}]

    # Run the stream and collect states
    states = []
    for step in collect_async(
        agentic_rag.aplan_and_solve_stream("Visual query", "Anime")
    ):
        if (
            isinstance(step, dict)
            and step["type"] == "thought"
            and "[State Machine]" in step["content"]
        ):
            states.append(step["content"])

    assert any("RAGState.VLM_RERANK" in s for s in states)


def agent_rag_plan_and_solve(service, query, media):
    # Helper to consume the stream and return final dict
    res = {}
    for step in collect_async(service.aplan_and_solve_stream(query, media)):
        if isinstance(step, dict) and step.get("type") == "token":
            res["answer"] = res.get("answer", "") + step["content"]
    return res


def test_thinking_mode_streaming(agentic_rag, mock_engine):
    # TTC indicates complex query
    agentic_rag._assess_complexity.return_value = (500, 3)

    plan = SearchPlan(
        optimized_query="complex query", requires_web=False, reasoning="R"
    )
    agentic_rag.planner.plan.return_value = plan
    agentic_rag.scout.find_truth_path.return_value = "Truth Path"

    outcome = DebateOutcome(
        consensus_action=JudgeAction.APPROVE, final_reasoning="ok", critiques={}
    )
    agentic_rag.debate_manager.conduct_debate.return_value = outcome

    # Synthesizer returns tokens including thought tags
    agentic_rag.synthesizer.asynthesize_stream.side_effect = as_async_iter(
        [
            InferenceResponse(text="<thought>"),
            InferenceResponse(text="Reasoning "),
            InferenceResponse(text="process"),
            InferenceResponse(text="</thought>"),
            InferenceResponse(text="Final "),
            InferenceResponse(text="Answer"),
        ]
    )

    steps = collect_async(agentic_rag.aplan_and_solve_stream("Complex query", "Anime"))

    # Check that thoughts are yielded as thoughts
    # Filter only thoughts from Synthesizer
    thoughts = [
        s["content"]
        for s in steps
        if isinstance(s, dict)
        and s["type"] == "thought"
        and "process" in str(s["content"])
    ]
    assert len(thoughts) > 0

    # Check that tokens are yielded as tokens
    tokens = "".join(
        [
            str(s["content"])
            for s in steps
            if isinstance(s, dict) and s["type"] == "token"
        ]
    )
    assert "Final Answer" in tokens
    assert "Reasoning" not in tokens


def test_fallback_on_inference_error(agentic_rag, mock_engine, mock_rag):
    from core.domain.exceptions import InferenceError  # noqa: E402

    # Mock planner to fail
    agentic_rag.planner.plan.side_effect = InferenceError("Inference failed!")

    # Fallback should trigger
    steps = collect_async(agentic_rag.aplan_and_solve_stream("Query", "Anime"))

    # Verify fallback state was reached
    assert any(
        "[Recovery] Erreur" in str(s["content"])
        for s in steps
        if isinstance(s, dict) and s["type"] == "thought"
    )
    assert any(
        "RAGState.FALLBACK_RAG" in str(s["content"])
        for s in steps
        if isinstance(s, dict) and s["type"] == "thought"
    )
