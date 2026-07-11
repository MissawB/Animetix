from unittest.mock import MagicMock

import pytest

from tests.helpers.agentic_rag_factory import build_test_agentic_rag_service
from tests.helpers.async_stream import as_async_iter

# Drives the full agentic RAG pipeline against a live inference engine (no ollama in CI).
pytestmark = pytest.mark.integration


@pytest.fixture
def mock_dependencies():
    return {
        "inference_engine": MagicMock(),
        "rag_service": MagicMock(),
        "web_search": MagicMock(),
        "prompt_manager": MagicMock(),
        "neo4j_manager": MagicMock(),
        "workflow_orchestrator": MagicMock(),
    }


def test_agentic_rag_triggers_thinking_mode_on_complex_query(mock_dependencies):
    """Test that AgenticRAGService enables thinking_mode when complexity >= 2."""
    # 1. Mock complexity analyzer to return high complexity
    mock_llm_service = MagicMock()
    mock_llm_service.generate.return_value = (
        '{"complexity_score": 2, "thinking_budget": 1000}'
    )

    # Fix: Mock prompt_manager to return (prompt, system)
    mock_dependencies["prompt_manager"].get_prompt.return_value = (
        "mock prompt",
        "mock system",
    )

    service = build_test_agentic_rag_service(
        **mock_dependencies, llm_service=mock_llm_service
    )

    # 2. Mock agents to check if they receive thinking_mode=True
    # The planner, critic, and synthesizer are initialized in __init__
    # We need to mock their plan/evaluate/synthesize methods
    service.planner = MagicMock()
    service.critic = MagicMock()
    service.synthesizer = MagicMock()

    # Setup synthesizer mock to yield something (it's an async generator)
    service.synthesizer.asynthesize_stream.side_effect = as_async_iter(["Response"])

    # Mock search and scouting to proceed to synthesis
    service.scout = MagicMock()
    service.critic.evaluate.return_value = MagicMock(
        is_relevant=True, suggested_action="PROCEED"
    )

    # Mock judge
    service.judge = MagicMock()
    service.judge.evaluate.return_value = MagicMock(
        is_reliable=True, hallucination_detected=False
    )

    # 3. Execute
    # We use plan_and_solve which calls plan_and_solve_stream
    service.plan_and_solve("Complex question about philosophy", "Anime")

    # 4. Verify that thinking_mode=True was passed to agents
    # In Task 5 implementation: thinking_mode = complexity >= 2
    # It is passed to planner.plan, critic.evaluate, and synthesizer.synthesize_stream

    # Check planner
    planner_args, planner_kwargs = service.planner.plan.call_args
    assert planner_kwargs["thinking_mode"] is True

    # Check synthesizer
    syn_args, syn_kwargs = service.synthesizer.asynthesize_stream.call_args
    assert syn_kwargs["thinking_mode"] is True
