import pytest
from unittest.mock import MagicMock
from core.domain.services.xai_service import XaiDiagnosticService, XaiCollector, UncertaintyService
from core.domain.entities.ai_schemas import InferenceResponse, InferenceMetadata, XaiReport, DocumentAttribution, ModelDiagnostics

@pytest.fixture
def mock_inference_engine():
    return MagicMock()

@pytest.fixture
def xai_service(mock_inference_engine):
    return XaiDiagnosticService(mock_inference_engine)

@pytest.fixture
def uncertainty_service(mock_inference_engine):
    return UncertaintyService(mock_inference_engine)

def test_generate_advanced_report(xai_service, mock_inference_engine):
    # Setup
    query = "Qui est Naruto ?"
    response_text = "Naruto est un ninja de Konoha."
    response = InferenceResponse(text=response_text, metadata=InferenceMetadata())
    
    collector = XaiCollector()
    collector.log_intent("information_retrieval")
    collector.log_retrieval([
        {"id": "doc1", "title": "Naruto Uzumaki", "score": 0.9},
        {"id": "doc2", "title": "Konoha", "score": 0.6}
    ])
    collector.log_agent_thought("RAG_Expert", "Searching for Naruto's origin.")

    mock_inference_engine.get_diagnostics.return_value = {
        "attention_heatmap": [[0.1, 0.2], [0.3, 0.4]],
        "top_attention_tokens": ["Naruto", "ninja"],
        "logit_lens": [{"layer": 1, "top_token": "Naruto", "prob": 0.8}]
    }
    
    # Mock UncertaintyService logic or inject it
    # For simplicity, we can mock calculate_uncertainty if xai_service uses it
    mock_inference_engine.calculate_uncertainty.return_value = {
        "normalized_entropy": 0.2,
        "perplexity": 1.5
    }

    # Execution
    report = xai_service.generate_advanced_report(query, response, collector)

    # Verifications
    assert isinstance(report, XaiReport)
    assert report.query_intent == "information_retrieval"
    assert len(report.retrieval_attribution) == 2
    assert report.retrieval_attribution[0].document_id == "doc1"
    assert report.retrieval_attribution[0].contribution_weight > 0
    
    assert isinstance(report.internal_diagnostics, ModelDiagnostics)
    assert report.internal_diagnostics.top_influential_tokens == ["Naruto", "ninja"]
    assert len(report.internal_diagnostics.logit_lens_trajectory) == 1
    assert report.internal_diagnostics.logit_lens_trajectory[0]["layer"] == 1

    assert report.uncertainty["confidence_score"] == 0.8
    assert len(report.agent_trace) == 1
    assert report.agent_trace[0]["agent"] == "RAG_Expert"
    assert report.final_confidence == 0.8
