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


def test_fallback_rag_processor_consumes_inferenceresponse():
    rag_service = MagicMock()
    rag_service.hybrid_search.return_value = []
    proc = FallbackRagProcessor(
        rag_service=rag_service, inference_engine=MagicMock(), expert_facts=[]
    )
    proc.inference_engine.stream_generate.return_value = iter(
        [InferenceResponse(text="ab"), InferenceResponse(text="cd")]
    )
    ctx = SimpleNamespace(
        query="q", media_type="Anime", language="Français", full_answer=""
    )

    steps = list(proc.process(ctx))

    tokens = [s for s in steps if s["type"] == "token"]
    assert "".join(s["content"] for s in tokens) == "abcd"
    assert ctx.full_answer == "abcd"
