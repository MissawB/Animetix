"""Native-async aprocess tests for the streaming RAG processors (SP2)."""

from types import SimpleNamespace  # noqa: F401
from unittest.mock import MagicMock

import pytest
from core.domain.entities.ai_schemas import InferenceResponse, RAGState  # noqa: F401
from core.domain.services.rag.agents.synthesizer import ResponseSynthesizer


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
