import pytest
from unittest.mock import MagicMock, patch
from adapters.inference.local_text_adapter import LocalTextAdapter
from adapters.inference.qwen3_vl_adapter import Qwen3VLAdapter
from adapters.inference.unified_inference_adapter import UnifiedInferenceAdapter
from adapters.inference.local_guardrail_adapter import LocalGuardrailAdapter

def test_local_text_adapter_moderate_content_keyword_fallback():
    # Instantiate without loading model
    adapter = LocalTextAdapter(model_id="fake-id")
    
    # Text with a bad word
    res = adapter.moderate_content("This content contains extreme violence and hentai.", ["INAPPROPRIATE"])
    
    assert res["is_safe"] is False
    assert "hentai" in res["detected_categories"]
    assert res["action"] == "block"
    assert "Vérification par mots-clés" in res["reason"]

    # Clean text
    res_clean = adapter.moderate_content("Hello Otaku! Welcome to Animetix.", ["INAPPROPRIATE"])
    assert res_clean["is_safe"] is True
    assert res_clean["action"] == "allow"

def test_qwen3_vl_adapter_moderate_content_keyword_fallback():
    # Setup adapter with a mock client
    with patch("adapters.inference.qwen3_vl_adapter.InferenceClient"):
        adapter = Qwen3VLAdapter(model_id="fake-qwen")
    
    # Text with a bad word
    res = adapter.moderate_content("This is NSFW content.", ["INAPPROPRIATE"])
    assert res["is_safe"] is False
    assert "nsfw" in res["detected_categories"]
    assert res["action"] == "block"

def test_local_text_adapter_moderate_content_semantic():
    adapter = LocalTextAdapter(model_id="fake-id")
    
    # Mock self.generate to return a structured JSON response
    mock_json_response = '{"is_safe": false, "detected_categories": ["SPOILER"], "reason": "Contains spoilers for Death Note."}'
    
    with patch.object(adapter, "generate", return_value=mock_json_response) as mock_gen:
        res = adapter.moderate_content("L dies in Death Note.", ["SPOILER"])
        
        assert res["is_safe"] is False
        assert "SPOILER" in res["detected_categories"]
        assert res["action"] == "block"
        assert "Contains spoilers for Death Note" in res["reason"]
        mock_gen.assert_called_once()

def test_unified_inference_adapter_moderate_content_semantic():
    adapter = UnifiedInferenceAdapter(api_base="http://fake-url", model_name="fake-model")
    
    # Mock generate to simulate semantic moderation response
    mock_json_response = '{"is_safe": true, "detected_categories": [], "reason": "Safe text"}'
    
    with patch.object(adapter, "generate", return_value=mock_json_response) as mock_gen:
        res = adapter.moderate_content("Let's talk about anime.", ["HATE_SPEECH"])
        
        assert res["is_safe"] is True
        assert res["detected_categories"] == []
        assert res["action"] == "allow"
        assert "Safe text" in res["reason"]

def test_local_guardrail_adapter_delegation():
    mock_engine = MagicMock()
    mock_engine.moderate_content.return_value = {"is_safe": True, "detected_categories": [], "action": "allow", "reason": "Engine checked"}
    
    adapter = LocalGuardrailAdapter(inference_engine=mock_engine)
    res = adapter.moderate_content("Test query", ["SPOILER"])
    
    assert res["is_safe"] is True
    assert res["reason"] == "Engine checked"
    mock_engine.moderate_content.assert_called_once_with("Test query", ["SPOILER"])
