"""
Single source of truth for Hugging Face model security: pinned revision (an
immutable commit SHA) and remote-code trust policy per model.

Merges the former `model_security.py` (get_verified_revision) and
`hf_security.py` (resolve_trust_remote_code / trusted_revision). A model gets
`trust_remote_code=True` ONLY if listed here with that flag, and is then pinned
to a real 40-hex SHA so a malicious future push cannot execute code.

`unsloth/DeepSeek-R1-Distill-Qwen-8B` and `kyutai/moshi-1b-preview` are
intentionally absent: they do not resolve on the Hub (RepositoryNotFoundError),
so they cannot be SHA-pinned and must not be trusted. Re-point the training
scripts / audio path at a resolvable, pinnable repo in a follow-up.
"""

import logging

from core.config import get_config

logger = logging.getLogger("animetix.security.models")


class ModelSecurityError(Exception):
    pass


# model_id -> {"revision": <40-hex SHA or None>, "trust_remote_code": bool}
# Revisions fetched from HfApi().model_info(id).sha. trust_remote_code=True
# requires a real SHA (enforced by tests).
MODELS: dict[str, dict] = {
    "jinaai/jina-embeddings-v3": {
        "revision": "ab036b023d30b4d1138c4c3bfa9f0c445ab455d6",
        "trust_remote_code": True,
    },
    "Remidesbois/LightonOCR-2-1b-poneglyph-bbox": {
        "revision": "8bdf97f30cb8006d17624407a847b6766fa2374b",
        "trust_remote_code": True,
    },
    "cvssp/audioldm-s-full-v2": {
        "revision": "feeb3d14203495a4b6ac0893cbdedb2159b4819c",
        "trust_remote_code": False,
    },
    "Qwen/Qwen2-VL-7B-Instruct": {
        "revision": "eed13092ef92e448dd6875b2a00151bd3f7db0ac",
        "trust_remote_code": False,
    },
    "Qwen/Qwen3-VL-8B-Instruct": {
        "revision": "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b",
        "trust_remote_code": False,
    },
    "Qwen/Qwen3-8B": {
        "revision": "b968826d9c46dd6066d109eabc6255188de91218",
        "trust_remote_code": False,
    },
    "Qwen/Qwen3-Embedding-8B": {
        "revision": "1d8ad4ca9b3dd8059ad90a75d4983776a23d44af",
        "trust_remote_code": False,
    },
    "Qwen/Qwen3-VL-Embedding-8B": {
        "revision": "2c4565515e0f265c6511776e7193b22c0968ddc7",
        "trust_remote_code": False,
    },
    "Qwen/Qwen3.5-4B": {
        "revision": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
        "trust_remote_code": False,
    },
    "Qwen/Qwen2.5-VL-7B-Instruct": {
        "revision": "cc594898137f460bfe9f0759e9844b3ce807cfb5",
        "trust_remote_code": False,
    },
    "black-forest-labs/FLUX.1-schnell": {
        "revision": "741f7c3ce8b383c54771c7003378a50191e9efe9",
        "trust_remote_code": False,
    },
    "HuggingFaceTB/SmolVLM-Instruct": {
        "revision": "81cd9a775a4d644f2faf4e7becff4559b46b14c7",
        "trust_remote_code": False,
    },
    "google/owlv2-base-patch16-ensemble": {
        "revision": "cfd3195ba4ea9592eec887ded089f4c08eff231d",
        "trust_remote_code": False,
    },
    "cross-encoder/ms-marco-MiniLM-L-12-v2": {
        "revision": "7b0235231ca2674cb8ca8f022859a6eba2b1c968",
        "trust_remote_code": False,
    },
    "Qwen/Qwen3-VL-30B-A3B-Instruct": {
        "revision": "9c4b90e1e4ba969fd3b5378b57d966d725f1b86c",
        "trust_remote_code": False,
    },
    "Qwen/Qwen3-0.6B": {
        "revision": "c1899de289a04d12100db370d81485cdf75e47ca",
        "trust_remote_code": False,
    },
    "HuggingFaceTB/SmolLM-135M": {
        "revision": "1d461723eec654e65efdc40cf49301c89c0c92f4",
        "trust_remote_code": False,
    },
}


def get_verified_revision(model_id: str) -> str | None:
    """Pinned SHA for a known model; STRICT mode blocks unknown models."""
    entry = MODELS.get(model_id)
    if entry and entry["revision"]:
        return entry["revision"]

    strict = get_config().get("STRICT_MODEL_VERIFICATION", False)
    msg = f"No verified signature found for model: {model_id}"
    if strict:
        logger.error(f"SECURITY ALERT: {msg}. Loading blocked.")
        raise ModelSecurityError(msg)
    logger.warning(f"SECURITY WARNING: {msg}. Loading unverified model.")
    return None


def resolve_trust_remote_code(model_id: str) -> bool:
    """True only for explicitly-allowlisted trusted models; False otherwise."""
    entry = MODELS.get(model_id)
    return bool(entry and entry["trust_remote_code"])


def trusted_revision(model_id: str) -> str | None:
    """Pinned SHA for a trusted model, else None (caller uses 'main')."""
    entry = MODELS.get(model_id)
    if entry and entry["trust_remote_code"]:
        return entry["revision"]
    return None
