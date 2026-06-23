"""
Single source of truth for Hugging Face remote-code trust.

`trust_remote_code=True` executes arbitrary Python from the model repo at load
time. A model is trusted ONLY if listed here, and is then loaded at an immutable
commit SHA so a future malicious push to that repo cannot run code. Everything
else defaults to False. Pure module — no Django, no torch.
"""

# model_id -> immutable commit SHA (40-hex). Fetched via huggingface_hub HfApi.
TRUSTED_REMOTE_CODE_MODELS: dict[str, str] = {
    "jinaai/jina-embeddings-v3": "ab036b023d30b4d1138c4c3bfa9f0c445ab455d6",
    "Remidesbois/LightonOCR-2-1b-poneglyph-bbox": "8bdf97f30cb8006d17624407a847b6766fa2374b",
}


def resolve_trust_remote_code(model_id: str) -> bool:
    """True only for explicitly-allowlisted models; False otherwise."""
    return model_id in TRUSTED_REMOTE_CODE_MODELS


def trusted_revision(model_id: str) -> str | None:
    """Pinned commit SHA for a trusted model, else None (caller uses 'main')."""
    return TRUSTED_REMOTE_CODE_MODELS.get(model_id)
