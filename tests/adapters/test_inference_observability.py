import pytest
from unittest.mock import MagicMock
from adapters.inference.unified_inference_adapter import UnifiedInferenceAdapter
from adapters.inference.fallback_adapter import FallbackInferenceAdapter

def test_unified_observability_success():
    adapter = UnifiedInferenceAdapter()
    
    # Test uncertainty calculations
    prompt = "Qui est Luffy ?"
    completion = "Luffy est le capitaine de l'équipage du chapeau de paille et souhaite devenir le roi des pirates."
    
    uncertainty = adapter.calculate_uncertainty(prompt, completion)
    
    assert "entropy" in uncertainty
    assert "perplexity" in uncertainty
    assert "confidence" in uncertainty
    assert isinstance(uncertainty["entropy"], float)
    assert isinstance(uncertainty["perplexity"], float)
    assert isinstance(uncertainty["confidence"], float)
    assert 0.0 <= uncertainty["confidence"] <= 1.0
    
    # Test diagnostics (Attention and Logit Lens)
    diagnostics = adapter.get_diagnostics(prompt, completion)
    
    assert "attention_map" in diagnostics
    assert "logit_lens" in diagnostics
    assert "model_signature" in diagnostics
    assert isinstance(diagnostics["attention_map"], list)
    assert len(diagnostics["logit_lens"]) > 0
    assert "Layer" in diagnostics["logit_lens"][0]["layer"]

def test_fallback_observability_routing():
    mock_adapter = MagicMock()
    mock_adapter.calculate_uncertainty.return_value = {
        "entropy": 1.25,
        "perplexity": 2.37,
        "confidence": 0.88
    }
    mock_adapter.get_diagnostics.return_value = {
        "attention_map": [[0.5, 0.5]],
        "logit_lens": [{"layer": "MockLayer", "confidence": 0.95}],
        "model_signature": "mock:signature"
    }
    
    fallback = FallbackInferenceAdapter(adapters=[mock_adapter])
    
    # Test fallback routing
    uncertainty = fallback.calculate_uncertainty("prompt", "completion")
    assert uncertainty["entropy"] == 1.25
    assert uncertainty["perplexity"] == 2.37
    mock_adapter.calculate_uncertainty.assert_called_once_with("prompt", "completion")
    
    diagnostics = fallback.get_diagnostics("prompt", "completion")
    assert diagnostics["model_signature"] == "mock:signature"
    mock_adapter.get_diagnostics.assert_called_once_with("prompt", "completion")
