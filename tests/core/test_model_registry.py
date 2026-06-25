import re

import pytest
from core.utils import model_registry as mr


def test_trusted_models_resolve_true_and_have_real_sha():
    for mid in (
        "jinaai/jina-embeddings-v3",
        "Remidesbois/LightonOCR-2-1b-poneglyph-bbox",
    ):
        assert mr.resolve_trust_remote_code(mid) is True
        assert re.fullmatch(r"[0-9a-f]{40}", mr.trusted_revision(mid)), mid


def test_untrusted_models_resolve_false():
    for mid in (
        "black-forest-labs/FLUX.1-schnell",
        "HuggingFaceTB/SmolVLM-Instruct",
        "Qwen/Qwen3-0.6B",
        "some/unknown-model",
    ):
        assert mr.resolve_trust_remote_code(mid) is False
    assert mr.trusted_revision("black-forest-labs/FLUX.1-schnell") is None


def test_get_verified_revision_returns_sha_for_known():
    assert mr.get_verified_revision("black-forest-labs/FLUX.1-schnell") == (
        "741f7c3ce8b383c54771c7003378a50191e9efe9"
    )


def test_get_verified_revision_unknown_non_strict_returns_none(monkeypatch):
    monkeypatch.setattr(mr, "get_config", lambda: {"STRICT_MODEL_VERIFICATION": False})
    assert mr.get_verified_revision("some/unknown-model") is None


def test_get_verified_revision_unknown_strict_raises(monkeypatch):
    monkeypatch.setattr(mr, "get_config", lambda: {"STRICT_MODEL_VERIFICATION": True})
    with pytest.raises(mr.ModelSecurityError):
        mr.get_verified_revision("some/unknown-model")


def test_every_trusted_entry_has_a_real_sha():
    for mid, entry in mr.MODELS.items():
        if entry["trust_remote_code"]:
            assert entry["revision"] and re.fullmatch(
                r"[0-9a-f]{40}", entry["revision"]
            ), f"{mid} is trusted but not SHA-pinned"


# ---------------------------------------------------------------------------
# Import-hygiene: the two legacy shim modules must no longer exist
# ---------------------------------------------------------------------------


def test_old_hf_security_module_is_gone():
    import importlib.util

    assert (
        importlib.util.find_spec("core.utils.hf_security") is None
    ), "core/utils/hf_security.py was not deleted; remove it and repoint consumers to model_registry"


def test_old_model_security_module_is_gone():
    import importlib.util

    assert (
        importlib.util.find_spec("core.utils.model_security") is None
    ), "core/utils/model_security.py was not deleted; remove it and repoint consumers to model_registry"


def test_repointed_models_present_and_pinned():
    assert mr.MODELS["unsloth/DeepSeek-R1-Distill-Qwen-7B"] == {
        "revision": "d53ce546e5539236bbadf12887371481c241ce6c",
        "trust_remote_code": True,
    }
    assert mr.MODELS["kyutai/moshiko-pytorch-bf16"] == {
        "revision": "2bfc9ae6e89079a5cc7ed2a68436010d91a3d289",
        "trust_remote_code": False,
    }


def test_dead_404_models_are_gone():
    assert "unsloth/DeepSeek-R1-Distill-Qwen-8B" not in mr.MODELS
    assert "kyutai/moshi-1b-preview" not in mr.MODELS


def test_siglip2_present_and_pinned():
    assert mr.MODELS["google/siglip2-so400m-patch14-384"] == {
        "revision": "e8e487298228002f3d8a82e0cd5c8ea9c567f57f",
        "trust_remote_code": False,
    }


def test_embedding_versions_map_resolves_to_known_models():
    assert mr.EMBEDDING_VERSIONS == {
        "text": {
            "v3": "jinaai/jina-embeddings-v3",
            "v4": "Qwen/Qwen3-Embedding-8B",
        },
        "vision": {
            "v2": "google/siglip2-so400m-patch14-384",
            "v3": "Qwen/Qwen3-VL-Embedding-8B",
        },
    }
    for kind in mr.EMBEDDING_VERSIONS.values():
        for model_id in kind.values():
            assert model_id in mr.MODELS, f"{model_id} not pinned in MODELS"
