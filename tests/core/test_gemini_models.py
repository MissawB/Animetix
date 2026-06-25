import importlib


def test_canonical_defaults():
    from core.utils import gemini_models as gm

    assert gm.GEMINI_FLASH == "gemini-3.5-flash"
    assert gm.GEMINI_LIVE == "gemini-live-2.5-flash-native-audio"
    assert gm.GEMINI_EMBEDDING == "gemini-embedding-2"


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("ANIMETIX_GEMINI_MODEL", "gemini-x")
    monkeypatch.setenv("ANIMETIX_GEMINI_LIVE_MODEL", "gemini-live-x")
    monkeypatch.setenv("ANIMETIX_GEMINI_EMBEDDING_MODEL", "gemini-embed-x")
    import core.utils.gemini_models as gm

    gm = importlib.reload(gm)
    assert gm.GEMINI_FLASH == "gemini-x"
    assert gm.GEMINI_LIVE == "gemini-live-x"
    assert gm.GEMINI_EMBEDDING == "gemini-embed-x"
