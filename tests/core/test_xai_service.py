import pytest
from unittest.mock import MagicMock
from core.domain.services.xai_service import XaiDiagnosticService, XaiCollector
from core.domain.entities.ai_schemas import (
    InferenceResponse,
    InferenceMetadata,
    XaiReport,
    ModelDiagnostics,
)


@pytest.fixture
def mock_inference_engine():
    return MagicMock()


@pytest.fixture
def xai_service(mock_inference_engine):
    return XaiDiagnosticService(mock_inference_engine)


def test_generate_advanced_report(xai_service, mock_inference_engine):
    # Setup
    query = "Qui est Naruto ?"
    response_text = "Naruto est un ninja de Konoha."

    # Mocking native logprobs
    from core.domain.entities.ai_schemas import TokenLogProb  # noqa: E402

    logprobs_data = [
        TokenLogProb(token="Naruto", logprob=-0.1, top_logprobs=[{"Naruto": -0.1}]),
        TokenLogProb(token=" ninja", logprob=-0.5, top_logprobs=[{" ninja": -0.5}]),
        TokenLogProb(token=" de", logprob=-0.01, top_logprobs=[{" de": -0.01}]),
    ]

    response = InferenceResponse(
        text=response_text, metadata=InferenceMetadata(logprobs=logprobs_data)
    )

    collector = XaiCollector()
    collector.log_intent("information_retrieval")
    collector.log_retrieval(
        [
            {"id": "doc1", "title": "Naruto Uzumaki", "score": 0.9},
            {"id": "doc2", "title": "Konoha", "score": 0.6},
        ]
    )
    collector.log_agent_thought("RAG_Expert", "Searching for Naruto's origin.")

    # Execution
    report = xai_service.generate_advanced_report(query, response, collector)

    # Verifications
    assert isinstance(report, XaiReport)
    assert report.query_intent == "information_retrieval"
    assert len(report.retrieval_attribution) == 2
    assert report.retrieval_attribution[0].document_id == "doc1"
    assert report.retrieval_attribution[0].contribution_weight > 0

    assert isinstance(report.internal_diagnostics, ModelDiagnostics)
    # Expected tokens based on sorting logprobs ascending
    assert report.internal_diagnostics.top_influential_tokens == [
        " ninja",
        "Naruto",
        " de",
    ]

    # Verify uncertainty calculation from logprobs
    assert report.uncertainty["method"] == "real_logprobs"
    assert report.uncertainty["confidence_score"] > 0
    assert len(report.internal_diagnostics.logit_lens_trajectory) == 0

    assert report.final_confidence > 0
    assert len(report.agent_trace) == 1
    assert report.agent_trace[0]["agent"] == "RAG_Expert"
