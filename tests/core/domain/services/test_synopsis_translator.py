from core.domain.services.synopsis_translator import SynopsisTranslator


def test_returns_empty_for_empty_input():
    assert SynopsisTranslator().translate_to_fr("Title", "") == ""


def test_returns_empty_when_no_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    # No key -> service must degrade gracefully, never raise, never call the network.
    assert (
        SynopsisTranslator().translate_to_fr(
            "Kimetsu no Yaiba", "It is the Taisho era."
        )
        == ""
    )
