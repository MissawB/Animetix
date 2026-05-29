import pytest
from unittest.mock import MagicMock, patch
from adapters.inference.local_guardrail_adapter import LocalGuardrailAdapter, ModerationResult

def test_semantic_moderation_success():
    mock_engine = MagicMock()
    mock_result = ModerationResult(
        is_safe=False,
        detected_categories=["nsfw", "violence"],
        reason="Contenu violent et explicite inapproprié."
    )
    mock_engine.generate_structured.return_value = mock_result
    
    adapter = LocalGuardrailAdapter(inference_engine=mock_engine)
    
    res = adapter.moderate_content(
        text="Quelque chose de inapproprié",
        categories=["nsfw", "violence"]
    )
    
    assert res["is_safe"] is False
    assert "nsfw" in res["detected_categories"]
    assert "violence" in res["detected_categories"]
    assert res["action"] == "block"
    assert res["reason"] == "Contenu violent et explicite inapproprié."
    mock_engine.generate_structured.assert_called_once()

def test_semantic_moderation_fallback_on_failure():
    mock_engine = MagicMock()
    mock_engine.generate_structured.side_effect = Exception("Connection timed out")
    
    adapter = LocalGuardrailAdapter(inference_engine=mock_engine)
    
    # Text with bad words should get blocked
    res = adapter.moderate_content(
        text="This contains hentai and porn content",
        categories=["nsfw"]
    )
    
    assert res["is_safe"] is False
    assert "hentai" in res["detected_categories"]
    assert res["action"] == "block"
    assert "Vérification par mots-clés" in res["reason"]
    
    # Safe text should pass
    res_safe = adapter.moderate_content(
        text="This is a very clean discussion about Naruto",
        categories=["nsfw"]
    )
    assert res_safe["is_safe"] is True
    assert len(res_safe["detected_categories"]) == 0
    assert res_safe["action"] == "allow"
