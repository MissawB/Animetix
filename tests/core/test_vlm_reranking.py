from unittest.mock import MagicMock

import pytest
from core.domain.entities.ai_schemas import JudgeAction, SearchPlan

from tests.helpers.agentic_rag_factory import build_test_agentic_rag_service

# Drives the full agentic RAG pipeline against a live inference engine (no ollama in CI).
pytestmark = pytest.mark.integration


@pytest.fixture
def mock_dependencies():
    inference_engine = MagicMock()
    rag_service = MagicMock()
    web_search = MagicMock()
    prompt_manager = MagicMock()
    llm_service = MagicMock()
    workflow_orchestrator = MagicMock()

    # Default prompt manager returns
    prompt_manager.get_prompt.return_value = ("prompt", "system")

    return (
        inference_engine,
        rag_service,
        web_search,
        prompt_manager,
        llm_service,
        workflow_orchestrator,
    )


def test_vlm_reranking_end_to_end(mock_dependencies):
    (
        inference_engine,
        rag_service,
        web_search,
        prompt_manager,
        llm_service,
        workflow_orchestrator,
    ) = mock_dependencies

    agentic_rag = build_test_agentic_rag_service(
        inference_engine=inference_engine,
        rag_service=rag_service,
        web_search=web_search,
        prompt_manager=prompt_manager,
        llm_service=llm_service,
        workflow_orchestrator=workflow_orchestrator,
    )

    # Force high confidence to skip fallback and librarian
    agentic_rag.uncertainty_service = MagicMock()
    agentic_rag.uncertainty_service.measure_confidence.return_value = {
        "confidence_score": 1.0,
        "is_reliable": True,
        "perplexity": None,
        "action_required": "PROCEED",
    }

    # 1. Mock complexity analyzer (TTC)
    llm_service.generate.return_value = (
        '{"complexity_score": 2, "thinking_budget": 100}'
    )

    # 2. Mock Planner returning is_visual_query=True
    mock_plan = SearchPlan(
        optimized_query="blue hair girl",
        requires_web=False,
        is_visual_query=True,
        reasoning="Looking for visual features",
    )
    llm_service.generate_structured.return_value = mock_plan

    # Mock synthesizer to return a high score directly if using ResponseSynthesizer
    # Actually, let's just patch CONDUCT_DEBATE too if it's used
    from core.domain.entities.ai_schemas import DebateOutcome  # noqa: E402

    outcome = DebateOutcome(
        consensus_action=JudgeAction.APPROVE, final_reasoning="Perfect", critiques={}
    )
    agentic_rag.debate_manager.conduct_debate = MagicMock(return_value=outcome)
    inference_engine.generate.side_effect = [
        "Initial truth path from Scout",  # Scout
        '{"is_reliable": true, "faithfulness_score": 1.0, "relevancy_score": 1.0, "hallucination_detected": false, "reasoning": "Perfect", "next_action": "APPROVE"}',  # Judge
    ]

    # Mock candidates from hybrid search
    # Candidate B (Black hair) is 1st (index 0)
    # Candidate A (Blue hair) is 2nd (index 1)
    rag_service.hybrid_search.return_value = [
        {
            "title": "Character B",
            "description": "A character with black hair.",
            "image_url": "http://example.com/black_hair.jpg",
        },
        {
            "title": "Character A",
            "description": "A character with blue hair.",
            "image_url": "http://example.com/blue_hair.jpg",
        },
    ]

    # Mock VLM Rerank swapping them
    # Character A (index 1) gets higher score
    inference_engine.visual_rerank.return_value = [
        {"index": 0, "score": 0.1},  # Character B
        {"index": 1, "score": 0.9},  # Character A
    ]

    # Mock Synthesizer stream
    inference_engine.stream_generate.return_value = iter(
        ["Final", " Answer", " mentioning", " Character", " A"]
    )

    # Run the process
    steps = list(
        agentic_rag.plan_and_solve_stream("Who is the girl with blue hair?", "Anime")
    )

    # Assertions

    # 1. Verify states reached
    states = [
        step["content"]
        for step in steps
        if step["type"] == "thought" and "[State Machine]" in step["content"]
    ]
    assert any(
        "État: RAGState.VLM_RERANK" in s for s in states
    ), "VLM_RERANK state was not reached"

    # 2. Verify visual_rerank was called with correct image URLs
    inference_engine.visual_rerank.assert_called_once()
    args, kwargs = inference_engine.visual_rerank.call_args
    # args[1] should be the image_urls
    assert "http://example.com/black_hair.jpg" in args[1]
    assert "http://example.com/blue_hair.jpg" in args[1]

    # 3. Verify the truth path passed to the synthesizer contains the reranked results
    # We need to capture the call to stream_generate which is used by ResponseSynthesizer
    inference_engine.stream_generate.assert_called_once()
    _, gen_kwargs = inference_engine.stream_generate.call_args
    # The first argument to stream_generate is the prompt which contains the context (truth_path)
    # Wait, the synthesizer gets syn_prompt, syn_sys.
    # Let's check what was passed to prompt_manager.get_prompt for synthesizer_final

    syn_call = None
    for call in prompt_manager.get_prompt.call_args_list:
        if call[0][0] == "synthesizer_final":
            syn_call = call
            break

    assert syn_call is not None
    context_passed = syn_call[1]["context"]

    # Verify that Character A is now ranked higher in the context
    # In _handle_vlm_rerank, it appends vlm_context to truth_path
    assert "### VÉRIFICATION VISUELLE (RERANKING) ###" in context_passed
    assert "1. Character A (Score Visuel: 0.90)" in context_passed
    assert "2. Character B (Score Visuel: 0.10)" in context_passed

    # 4. Verify the final answer is correct
    final_answer = "".join(
        [step["content"] for step in steps if step["type"] == "token"]
    )
    assert "Final Answer mentioning Character A" == final_answer
