import sentence_transformers
from core.utils.model_registry import get_verified_revision
from pipeline import models_registry as mr_mod


def _patch_loader(monkeypatch):
    captured = {}

    class FakeST:
        def __init__(self, model_id, **kwargs):
            captured["model_id"] = model_id
            captured["kwargs"] = kwargs

    monkeypatch.setattr(sentence_transformers, "SentenceTransformer", FakeST)
    monkeypatch.setattr(
        mr_mod.ModelIntegrityVerifier,
        "verify",
        staticmethod(lambda model_id, revision=None: None),
    )
    return captured


def test_text_model_v3_uses_registry_revision_not_manifest(monkeypatch):
    captured = _patch_loader(monkeypatch)
    reg = mr_mod.ModelsRegistry()
    reg._device = "cpu"
    reg.active_text_version = "v3"  # jina — the drift-prone one
    _ = reg.text_model
    assert captured["model_id"] == "jinaai/jina-embeddings-v3"
    assert captured["kwargs"]["revision"] == get_verified_revision(
        "jinaai/jina-embeddings-v3"
    )
    assert captured["kwargs"]["revision"] == "ab036b023d30b4d1138c4c3bfa9f0c445ab455d6"
    assert captured["kwargs"]["trust_remote_code"] is True  # jina is trusted


def test_vision_model_v3_resolves_registry_revision(monkeypatch):
    captured = _patch_loader(monkeypatch)
    reg = mr_mod.ModelsRegistry()
    reg._device = "cpu"
    reg.active_vision_version = "v3"  # Qwen3-VL-Embedding-8B
    _ = reg.vision_model
    assert captured["model_id"] == "Qwen/Qwen3-VL-Embedding-8B"
    assert captured["kwargs"]["revision"] == get_verified_revision(
        "Qwen/Qwen3-VL-Embedding-8B"
    )
    assert captured["kwargs"]["trust_remote_code"] is False
