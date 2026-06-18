import pytest
from backend.core.utils.model_security import get_verified_revision, ModelSecurityError


def test_get_verified_revision_returns_sha():
    # Assuming 'cvssp/audioldm-s-full-v2' is in the registry
    sha = get_verified_revision("cvssp/audioldm-s-full-v2")
    assert isinstance(sha, str)
    assert len(sha) == 40  # Standard git SHA length


def test_get_verified_revision_raises_error_in_strict_mode(settings):
    settings.STRICT_MODEL_VERIFICATION = True
    with pytest.raises(ModelSecurityError):
        get_verified_revision("malicious/unverified-model")
