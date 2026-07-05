from unittest.mock import MagicMock, patch

import pytest
from core.domain.entities.ai_schemas import (
    DebateOutcome,
    InferenceResponse,
    JudgeAction,
    SearchPlan,
)

from tests.helpers.agentic_rag_factory import build_test_agentic_rag_service

# Drives the full agentic RAG pipeline against a live inference engine (no ollama in CI).
pytestmark = pytest.mark.integration


@pytest.fixture
def mock_dependencies():
    inference_engine = MagicMock()
    rag_service = MagicMock()
    web_search = MagicMock()
    prompt_manager = MagicMock()

    # Mock for complexity analysis
    prompt_manager.get_prompt.return_value = ("prompt", "system")
    inference_engine.generate.return_value = (
        '{"thinking_budget": 100, "complexity_score": 3}'
    )

    return inference_engine, rag_service, web_search, prompt_manager


def test_librarian_loop_integration(mock_dependencies):
    inference_engine, rag_service, web_search, prompt_manager = mock_dependencies

    # Setup mocks
    uncertainty_service = MagicMock()
    uncertainty_service.measure_confidence.return_value = 0.3  # Low confidence

    librarian = MagicMock()
    librarian.identify_gap.return_value = {
        "missing_fact": "Date",
        "source_type": "JIKAN",
        "query": "Naruto Ep 5",
    }
    librarian.fetch_data.return_value = "Date: 2002-10-31"

    # Planner mock
    planner = MagicMock()
    planner.plan.return_value = SearchPlan(
        optimized_query="Naruto Ep 5", reasoning="Need to find info", requires_web=True
    )

    # Synthesizer mock: side_effect gives each synthesis pass (before/after Librarian)
    # a fresh iterator of InferenceResponse chunks (SynthesizeProcessor reads .text).
    synthesizer = MagicMock()
    synthesizer.synthesize_stream.side_effect = lambda *a, **k: iter(
        [InferenceResponse(text="C'est un anime.")]
    )

    # DebateManager mock
    debate_manager = MagicMock()
    debate_manager.conduct_debate.return_value = DebateOutcome(
        critiques={},
        consensus_action=JudgeAction.APPROVE,
        final_reasoning="Good enough after librarian",
    )

    # AgenticRAGService instantiation
    service = build_test_agentic_rag_service(
        inference_engine=inference_engine,
        rag_service=rag_service,
        web_search=web_search,
        prompt_manager=prompt_manager,
        llm_service=MagicMock(),
        workflow_orchestrator=MagicMock(),
        uncertainty_service=uncertainty_service,
        librarian=librarian,
        debate_manager=debate_manager,
    )

    # Override internal agents to avoid real LLM calls if they weren't passed to init
    service.planner = planner
    service.synthesizer = synthesizer

    # Search execution mock
    with patch.object(service, "_execute_search", return_value=([], "Initial context")):
        # Scout mock
        service.scout = MagicMock()
        service.scout.find_truth_path.return_value = "Distilled context"

        # Run the stream
        events = list(
            service.plan_and_solve_stream("Quand est sorti Naruto Ep 5 ?", "anime")
        )

        # Verification
        thoughts = [e["content"] for e in events if e["type"] == "thought"]
        print("DEBUG THOUGHTS:", thoughts)

        # 1. Assert that ACQUIRE_KNOWLEDGE was reached
        assert any(
            "[Librarian] Recherche active sur JIKAN : Naruto Ep 5" in t
            for t in thoughts
        )
        assert any(
            "[Uncertainty] Basse confiance détectée (0.30). Déclenchement du Librarian..."
            in t
            for t in thoughts
        )

        # 2. Verify that the second synthesis starts (implied by the state machine flow)
        # Synthesizer is called twice: once before Librarian, once after.
        assert synthesizer.synthesize_stream.call_count == 2

        # 3. Assert that truth_path (injected in fetch_data) is present
        # Since I can't easily access ctx from outside, I check if librarian.fetch_data was called
        librarian.fetch_data.assert_called_once()

        # Verify that the final consensus was reached
        assert any("Consensus :" in t and "APPROVE" in t for t in thoughts)


if __name__ == "__main__":
    # Small manual run helper
    pytest.main([__file__])
