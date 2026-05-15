import pytest
from unittest.mock import MagicMock
from core.domain.services.xai_service import XaiDiagnosticService, UncertaintyService

@pytest.fixture
def mock_engine():
    return MagicMock()

@pytest.fixture
def xai_service(mock_engine):
    return XaiDiagnosticService(inference_engine=mock_engine)

@pytest.fixture
def uncertainty_service(mock_engine):
    return UncertaintyService(inference_engine=mock_engine)

def test_explain_response(xai_service, mock_engine):
    mock_engine.get_diagnostics.return_value = {
        "top_attention_tokens": ["Naruto", "ninja"],
        "logit_lens_trend": "increasing"
    }
    res = xai_service.explain_response("q", "c")
    assert "Naruto, ninja" in res["explanation"]
    assert res["logit_lens_trend"] == "increasing"

def test_measure_confidence_reliable(uncertainty_service, mock_engine):
    mock_engine.calculate_uncertainty.return_value = {
        "normalized_entropy": 0.1,
        "perplexity": 1.2
    }
    res = uncertainty_service.measure_confidence("q", "c")
    assert res["confidence_score"] == pytest.approx(0.9)
    assert res["is_reliable"] is True
    assert res["action_required"] == "PROCEED"

def test_measure_confidence_unreliable(uncertainty_service, mock_engine):
    mock_engine.calculate_uncertainty.return_value = {
        "normalized_entropy": 0.5,
        "perplexity": 10.0
    }
    res = uncertainty_service.measure_confidence("q", "c")
    assert res["confidence_score"] == pytest.approx(0.5)
    assert res["is_reliable"] is False
    assert res["action_required"] == "VERIFY_WEB"
