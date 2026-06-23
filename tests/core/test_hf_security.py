import re

from core.utils import hf_security as hs


def test_trusted_models_are_allowlisted():
    assert hs.resolve_trust_remote_code("jinaai/jina-embeddings-v3") is True
    assert (
        hs.resolve_trust_remote_code("Remidesbois/LightonOCR-2-1b-poneglyph-bbox")
        is True
    )


def test_untrusted_models_default_to_false():
    for model_id in (
        "black-forest-labs/FLUX.1-schnell",
        "HuggingFaceTB/SmolVLM-Instruct",
        "Qwen/Qwen3.5-4B",
        "Qwen/Qwen3-VL-8B-Instruct",
        "some/unknown-model",
    ):
        assert hs.resolve_trust_remote_code(model_id) is False


def test_trusted_revision_is_pinned_immutable_sha():
    sha = hs.trusted_revision("jinaai/jina-embeddings-v3")
    assert sha is not None and re.fullmatch(
        r"[0-9a-f]{40}", sha
    ), "trusted models must pin a 40-hex immutable commit SHA, not a branch"
    assert hs.trusted_revision("Remidesbois/LightonOCR-2-1b-poneglyph-bbox") is not None


def test_untrusted_revision_is_none():
    assert hs.trusted_revision("HuggingFaceTB/SmolVLM-Instruct") is None
    assert hs.trusted_revision("some/unknown-model") is None
