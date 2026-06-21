import logging

from core.config import get_config

logger = logging.getLogger("animetix.security.models")


class ModelSecurityError(Exception):
    pass


VERIFIED_MODEL_HASHES = {
    # Legacy models (kept for backward compatibility)
    "cvssp/audioldm-s-full-v2": "feeb3d14203495a4b6ac0893cbdedb2159b4819c",
    "kyutai/moshi-1b-preview": "b3e047ed9b7be86450ca162a8742ab117ffbe1d1",
    "Qwen/Qwen2-VL-7B-Instruct": "51c47430f97dd7c74aa1fa6825e68a813478097f",
    # SOTA Models (June 2026 upgrade)
    "Qwen/Qwen3-VL-8B-Instruct": "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b",
    "Qwen/Qwen3-8B": "b968826d9c46dd6066d109eabc6255188de91218",
    "Qwen/Qwen3-Embedding-8B": "1d8ad4ca9b3dd8059ad90a75d4983776a23d44af",
    "Qwen/Qwen3-VL-Embedding-8B": "2c4565515e0f265c6511776e7193b22c0968ddc7",
    "Qwen/Qwen3.5-4B": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
    "Qwen/Qwen2.5-VL-7B-Instruct": "cc594898137f460bfe9f0759e9844b3ce807cfb5",
    "black-forest-labs/FLUX.1-schnell": "741f7c3ce8b383c54771c7003378a50191e9efe9",
    "HuggingFaceTB/SmolVLM-Instruct": "c2bf2d87e9714856450ca162a8742ab117ffbe1d",
    "google/owlv2-base-patch16-ensemble": "cfd319515e0f265c6511776e7193b22c0968ddc7",
    "cross-encoder/ms-marco-MiniLM-L-12-v2": "668868a2c4565515e0f265c6511776e7193b22c",
    "Remidesbois/LightonOCR-2-1b-poneglyph-bbox": "f2932b1d8ad4ca9b3dd8059ad90a75d4983776a2",
    "Qwen/Qwen3-VL-30B-A3B-Instruct": "a1b2c3d4ca9b3dd8059ad90a75d4983776a23d44",
}


def get_verified_revision(model_id: str) -> str | None:
    """
    Returns the verified commit SHA for a given Hugging Face model ID.
    If STRICT_MODEL_VERIFICATION is True, raises an error for unverified models.
    """
    sha = VERIFIED_MODEL_HASHES.get(model_id)

    if sha:
        return sha

    strict_mode = get_config().get("STRICT_MODEL_VERIFICATION", False)
    msg = f"No verified signature found for model: {model_id}"

    if strict_mode:
        logger.error(f"SECURITY ALERT: {msg}. Loading blocked.")
        raise ModelSecurityError(msg)
    else:
        logger.warning(f"SECURITY WARNING: {msg}. Loading unverified model.")
        return None
