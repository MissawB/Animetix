import pytest
from unittest.mock import MagicMock
from core.domain.services.agentic_rag_service import AgenticRAGService
from core.domain.entities.ai_schemas import (
    ForgeHypothesis,
    DebateOutcome,
    JudgeAction,
    SearchPlan,
)


@pytest.fixture
def mock_engine():
    engine = MagicMock()
    engine.stream_generate.return_value = iter(["Generated ", "answer."])
    return engine


@pytest.fixture
def mock_rag():
    rag = MagicMock()
    rag.hybrid_search.return_value = [
        {"title": "Local Info", "description": "Some local data"}
    ]
    return rag


@pytest.fixture
def mock_web():
    return MagicMock()


@pytest.fixture
def mock_prompt_manager():
    pm = MagicMock()
    pm.get_prompt.return_value = ("prompt", "system")
    return pm


@pytest.fixture
def mock_librarian():
    return MagicMock()


@pytest.fixture
def mock_forge():
    return MagicMock()


@pytest.fixture
def mock_uncertainty():
    return MagicMock()


@pytest.fixture
def mock_debate_manager():
    return MagicMock()


@pytest.fixture
def agentic_rag(
    mock_engine,
    mock_rag,
    mock_web,
    mock_prompt_manager,
    mock_librarian,
    mock_forge,
    mock_uncertainty,
    mock_debate_manager,
):
    service = AgenticRAGService(
        inference_engine=mock_engine,
        rag_service=mock_rag,
        web_search=mock_web,
        prompt_manager=mock_prompt_manager,
        llm_service=MagicMock(),
        workflow_orchestrator=MagicMock(),
        librarian=mock_librarian,
        forge=mock_forge,
        uncertainty_service=mock_uncertainty,
        debate_manager=mock_debate_manager,
    )
    # Mock internally initialized agents to avoid extra LLM calls
    service.planner = MagicMock()
    service.scout = MagicMock()
    service.synthesizer = MagicMock()
    service.judge = MagicMock()
    return service


def test_forge_speculation_e2e(
    agentic_rag,
    mock_engine,
    mock_librarian,
    mock_forge,
    mock_uncertainty,
    mock_debate_manager,
):
    """
    Test end-to-end: Uncertainty triggers Librarian -> Librarian fails -> Forge speculates.
    """
    # 1. Setup Complexity and Planner
    # In plan_and_solve_stream, _assess_complexity is called.
    # But it uses self.llm_service which uses self.inference_engine.
    # We can mock _assess_complexity directly or mock the llm_service call.
    agentic_rag._assess_complexity = MagicMock(return_value=(0, 0))

    # 2. Setup Planner
    agentic_rag.planner.plan.return_value = SearchPlan(
        optimized_query="test query",
        requires_web=False,
        reasoning="Testing speculation",
    )

    # 3. Setup Scout
    agentic_rag.scout.find_truth_path.return_value = "Initial truth path"

    # 4. Setup Synthesizer (first pass)
    agentic_rag.synthesizer.synthesize_stream.return_value = iter(
        ["First ", "attempt."]
    )

    # 5. Setup Uncertainty (trigger Librarian)
    mock_uncertainty.measure_confidence.return_value = 0.4

    # 6. Setup Librarian (identify gap but fail fetch)
    mock_librarian.identify_gap.return_value = {
        "query": "missing detail",
        "source_type": "Web",
    }
    mock_librarian.fetch_data.return_value = None  # This triggers SPECULATE

    # 7. Setup Forge
    mock_forge.generate_hypothesis.return_value = ForgeHypothesis(
        hypothesis="Forged hypothesis",
        rationale="Deduced from patterns",
        confidence=0.8,
    )

    # 8. Setup Synthesizer (second pass, after speculation)
    agentic_rag.synthesizer.synthesize_stream.side_effect = [
        iter(["First ", "attempt."]),
        iter(["Final ", "answer ", "with ", "speculation."]),
    ]

    # 9. Setup Debate Manager (Approve final answer)
    mock_debate_manager.conduct_debate.return_value = DebateOutcome(
        critiques={}, consensus_action=JudgeAction.APPROVE, final_reasoning="Looks good"
    )

    # Execute
    events = list(
        agentic_rag.plan_and_solve_stream("Will GTA 6 be on PC at launch?", "Game")
    )

    # Extract thought contents
    thoughts = [e["content"] for e in events if e["type"] == "thought"]

    # Assertions
    assert any("[Uncertainty] Basse confiance détectée" in t for t in thoughts)
    assert any(
        "[Librarian] Aucune donnée supplémentaire trouvée. Passage en mode spéculation..."
        in t
        for t in thoughts
    )
    assert any(
        "[The Forge] Hypothèse générée : Forged hypothesis" in t for t in thoughts
    )

    # Check final answer
    final_answer = "".join([e["content"] for e in events if e["type"] == "token"])
    assert "Final answer with speculation." in final_answer

    # Verify transitions
    states = [t for t in thoughts if "[State Machine]" in t]
    assert any("État: RAGState.ACQUIRE_KNOWLEDGE" in s for s in states)
    assert any("État: RAGState.SPECULATE" in s for s in states)
    assert any("État: RAGState.SYNTHESIZE" in s for s in states)

    # Verify that synthesizer was called with the hypothesis in context
    # It should be called twice: once before Librarian, once after Forge
    assert agentic_rag.synthesizer.synthesize_stream.call_count == 2
    last_call_args = agentic_rag.synthesizer.synthesize_stream.call_args_list[-1]
    args, kwargs = last_call_args
    # Context is the second positional argument
    context = args[1]
    assert "Forged hypothesis" in context
    assert "DÉDUCTION :" in context
