import logging
from django.conf import settings

logger = logging.getLogger('animetix.security.models')

class ModelSecurityError(Exception):
    pass

VERIFIED_MODEL_HASHES = {
    "cvssp/audioldm-s-full-v2": "feeb3d14203495a4b6ac0893cbdedb2159b4819c",
    "kyutai/moshi-1b-preview": "b3e047ed9b7be86450ca162a8742ab117ffbe1d1",
    "Qwen/Qwen2-VL-7B-Instruct": "51c47430f97dd7c74aa1fa6825e68a813478097f",
    # Add other core models here
}

def get_verified_revision(model_id: str) -> str | None:
    """
    Returns the verified commit SHA for a given Hugging Face model ID.
    If STRICT_MODEL_VERIFICATION is True, raises an error for unverified models.
    """
    sha = VERIFIED_MODEL_HASHES.get(model_id)
    
    if sha:
        return sha
        
    strict_mode = getattr(settings, 'STRICT_MODEL_VERIFICATION', False)
    msg = f"No verified signature found for model: {model_id}"
    
    if strict_mode:
        logger.error(f"SECURITY ALERT: {msg}. Loading blocked.")
        raise ModelSecurityError(msg)
    else:
        logger.warning(f"SECURITY WARNING: {msg}. Loading unverified model.")
        return None
