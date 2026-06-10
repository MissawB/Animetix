# Hugging Face Model Signature Verification Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement supply chain security for AI models by verifying Hugging Face commit SHAs before loading them.

**Architecture:** Create a central security registry (`model_security.py`) and update existing `InferenceAdapters` to pass the `revision` parameter to `from_pretrained`.

**Tech Stack:** Python 3.10+, Django Settings, `transformers`, `diffusers`.

---

### Task 1: Centralized Model Security Registry

**Files:**
- Create: `backend/core/utils/model_security.py`
- Modify: `backend/api/animetix_project/settings.py`
- Test: `tests/core/utils/test_model_security.py`

- [X] **Step 1: Write failing test**

```python
import pytest
from backend.core.utils.model_security import get_verified_revision, ModelSecurityError
from django.conf import settings

def test_get_verified_revision_returns_sha():
    # Assuming 'cvssp/audioldm-s-full-v2' is in the registry
    sha = get_verified_revision("cvssp/audioldm-s-full-v2")
    assert isinstance(sha, str)
    assert len(sha) == 40 # Standard git SHA length

def test_get_verified_revision_raises_error_in_strict_mode(settings):
    settings.STRICT_MODEL_VERIFICATION = True
    with pytest.raises(ModelSecurityError):
        get_verified_revision("malicious/unverified-model")
```

- [X] **Step 2: Add setting to `settings.py`**
Add `STRICT_MODEL_VERIFICATION = False` to `backend/api/animetix_project/settings.py`.

- [X] **Step 3: Implement `model_security.py`**

```python
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
```

- [X] **Step 4: Run tests and verify PASS**

- [X] **Step 5: Commit**

```bash
git add backend/core/utils/model_security.py backend/api/animetix_project/settings.py tests/core/utils/test_model_security.py
git commit -m "feat(security): implement model signature verification registry"
```

---

### Task 2: Secure Core Adapters (Audio & Vision)

**Files:**
- Modify: `backend/adapters/inference/audio_mixin.py`
- Modify: `backend/adapters/inference/qwen3_vl_adapter.py`

- [X] **Step 1: Update `AudioMixin`**
Modify `_load_audioldm` and `_load_moshi` in `backend/adapters/inference/audio_mixin.py` to use `get_verified_revision`.

```python
# In _load_audioldm:
from core.utils.model_security import get_verified_revision
model_id = "cvssp/audioldm-s-full-v2"
revision = get_verified_revision(model_id)
self._audioldm_pipeline = AudioLDMPipeline.from_pretrained(
    model_id, 
    revision=revision,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
)
```
(Do the same for `moshi-1b-preview` in `_load_moshi`).

- [X] **Step 2: Update `Qwen3VLAdapter`**
Modify `get_vision_text_completion` in `backend/adapters/inference/qwen3_vl_adapter.py` to use the helper when initializing the `InferenceClient`.

```python
from core.utils.model_security import get_verified_revision
# ...
revision = get_verified_revision(self.model_id)
client = InferenceClient(model=self.model_id, token=os.getenv("HUGGINGFACE_API_KEY"), revision=revision)
```

- [X] **Step 3: Run existing adapter tests to ensure no breakage**
Run `pytest tests/adapters/test_creative_inference.py` and `pytest tests/adapters/test_s2s_inference.py`.

- [X] **Step 4: Commit**

```bash
git add backend/adapters/inference/audio_mixin.py backend/adapters/inference/qwen3_vl_adapter.py
git commit -m "feat(security): enforce model signatures in Audio and Vision adapters"
```
