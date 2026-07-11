"""Regression tests for the InferenceResponse-vs-.text bug in RAG stream processors.

The inference engine / synthesizer yield InferenceResponse objects; the processors
must read `.text`. Each test feeds real InferenceResponse chunks (the contract) and
asserts correct string assembly into StreamStep `token` frames.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from core.domain.entities.ai_schemas import InferenceResponse
from core.domain.services.rag.processors.fallback_rag_processor import (
    FallbackRagProcessor,
)
from core.domain.services.rag.processors.synthesize_processor import SynthesizeProcessor

from tests.helpers.async_stream import as_async_iter, collect_async


def test_fallback_rag_processor_consumes_inferenceresponse():
    rag_service = MagicMock()
    rag_service.hybrid_search.return_value = []
    proc = FallbackRagProcessor(
        rag_service=rag_service, inference_engine=MagicMock(), expert_facts=[]
    )
    proc.inference_engine.astream_generate.side_effect = as_async_iter(
        [InferenceResponse(text="ab"), InferenceResponse(text="cd")]
    )
    ctx = SimpleNamespace(
        query="q", media_type="Anime", language="Français", full_answer=""
    )

    steps = collect_async(proc.aprocess(ctx))

    tokens = [s for s in steps if s["type"] == "token"]
    assert "".join(s["content"] for s in tokens) == "abcd"
    assert ctx.full_answer == "abcd"


def test_synthesize_processor_consumes_inferenceresponse():
    synthesizer = MagicMock()
    synthesizer.asynthesize_stream.side_effect = as_async_iter(
        [InferenceResponse(text="Hello "), InferenceResponse(text="world")]
    )
    proc = SynthesizeProcessor(synthesizer=synthesizer, xai_service=MagicMock())
    ctx = SimpleNamespace(
        query="q",
        truth_path="ctx",
        thinking_budget=0,
        thinking_mode=False,
        use_slm=False,
        correction_feedback=None,
        language="Français",
        full_answer="",
        knowledge_acquired=True,  # skip the measure_confidence branch
    )

    steps = collect_async(proc.aprocess(ctx))

    tokens = [s for s in steps if s["type"] == "token"]
    assert "".join(s["content"] for s in tokens) == "Hello world"
    assert ctx.full_answer == "Hello world"
