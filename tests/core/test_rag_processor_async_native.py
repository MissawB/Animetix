"""Native-async aprocess tests for the streaming RAG processors (SP2)."""

from types import SimpleNamespace  # noqa: F401
from unittest.mock import MagicMock

import pytest
from core.domain.entities.ai_schemas import InferenceResponse, RAGState  # noqa: F401
from core.domain.services.rag.agents.synthesizer import ResponseSynthesizer
from core.domain.services.rag.processors.fallback_rag_processor import (
    FallbackRagProcessor,
)
from core.domain.services.rag.processors.synthesize_processor import (
    SynthesizeProcessor,
)


async def _aiter(items):
    for it in items:
        yield it


@pytest.mark.asyncio
async def test_asynthesize_stream_yields_chunks_and_forwards_params():
    llm = MagicMock()
    llm.astream_generate.return_value = _aiter(
        [InferenceResponse(text="Hello "), InferenceResponse(text="world")]
    )
    prompt_manager = MagicMock()
    prompt_manager.get_prompt.return_value = ("PROMPT", "SYS")
    synth = ResponseSynthesizer(llm_service=llm, prompt_manager=prompt_manager)

    chunks = [
        c.text
        async for c in synth.asynthesize_stream(
            "q", "ctx", thinking_budget=7, thinking_mode=True, use_slm=True
        )
    ]

    assert chunks == ["Hello ", "world"]
    _, kwargs = llm.astream_generate.call_args
    assert kwargs["use_slm"] is True
    assert kwargs["thinking_budget"] == 7
    assert kwargs["thinking_mode"] is True


@pytest.mark.asyncio
async def test_fallback_rag_aprocess_streams_and_sets_finalize():
    rag_service = MagicMock()
    rag_service.hybrid_search.return_value = [{"title": "T", "description": "D"}]
    engine = MagicMock()
    engine.astream_generate.return_value = _aiter(
        [InferenceResponse(text="ab"), InferenceResponse(text="cd")]
    )
    proc = FallbackRagProcessor(
        rag_service=rag_service, inference_engine=engine, expert_facts=[]
    )
    ctx = SimpleNamespace(
        query="q",
        media_type="Anime",
        language="Français",
        full_answer="",
        next_state=None,
    )

    steps = [s async for s in proc.aprocess(ctx)]

    tokens = [s for s in steps if s["type"] == "token"]
    assert "".join(s["content"] for s in tokens) == "abcd"
    assert ctx.full_answer == "abcd"
    assert any(s["type"] == "thought" for s in steps)
    assert ctx.next_state == RAGState.FINALIZE
    rag_service.hybrid_search.assert_called_once_with("q", "Anime")


def _synth_ctx(**overrides):
    base = dict(
        query="q",
        truth_path="ctx",
        thinking_budget=0,
        thinking_mode=False,
        use_slm=False,
        correction_feedback=None,
        language="Français",
        full_answer="",
        knowledge_acquired=False,
        next_state=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.mark.asyncio
async def test_synthesize_aprocess_parses_thought_tags_and_judges():
    synthesizer = MagicMock()
    synthesizer.asynthesize_stream.return_value = _aiter(
        [
            InferenceResponse(text="Hi "),
            InferenceResponse(text="<thought>"),
            InferenceResponse(text="plan"),
            InferenceResponse(text="</thought>"),
            InferenceResponse(text=" bye"),
        ]
    )
    xai = MagicMock()
    xai.measure_confidence.return_value = {"confidence_score": 0.9}
    proc = SynthesizeProcessor(synthesizer=synthesizer, xai_service=xai)
    ctx = _synth_ctx()

    steps = [s async for s in proc.aprocess(ctx)]

    tokens = "".join(s["content"] for s in steps if s["type"] == "token")
    thoughts = [s["content"] for s in steps if s["type"] == "thought"]
    assert "Hi " in tokens and " bye" in tokens
    assert ctx.full_answer == "Hi  bye"
    assert any("plan" in t for t in thoughts)
    assert ctx.next_state == RAGState.JUDGE


@pytest.mark.asyncio
async def test_synthesize_aprocess_low_confidence_acquires_knowledge():
    synthesizer = MagicMock()
    synthesizer.asynthesize_stream.return_value = _aiter(
        [InferenceResponse(text="answer")]
    )
    xai = MagicMock()
    xai.measure_confidence.return_value = {"confidence_score": 0.3}
    proc = SynthesizeProcessor(synthesizer=synthesizer, xai_service=xai)
    ctx = _synth_ctx()

    steps = [s async for s in proc.aprocess(ctx)]

    assert ctx.knowledge_acquired is True
    assert ctx.next_state == RAGState.ACQUIRE_KNOWLEDGE
    assert any(s["type"] == "thought" and "Uncertainty" in s["content"] for s in steps)
