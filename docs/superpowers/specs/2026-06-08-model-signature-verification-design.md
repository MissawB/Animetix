# Design Specification: Hugging Face Model Signature Verification

Ensuring supply chain security for AI models loaded from the Hugging Face Hub by verifying their signatures (commit SHAs) before loading weights into memory.

## 1. Vision & Purpose
Machine learning models are essentially executable binaries. Loading compromised weights (e.g., via a hijacked Hugging Face repository or a malicious PR) can lead to arbitrary code execution or poisoned outputs. To prevent this, we must pin our model downloads to verified commit hashes (SHAs).

## 2. Technical Architecture

### Centralized Security Registry
- **File:** `backend/core/utils/model_security.py`
- **Component:** `ModelSignatureVerifier`
- **Functionality:** 
  - Maintains a hardcoded registry of `model_id` to `verified_sha`.
  - Provides a helper method `get_verified_revision(model_id: str) -> str`.
  - Depending on the `STRICT_MODEL_VERIFICATION` Django setting, it will either enforce the hash (raising a `SecurityError` if missing or mismatched) or log a critical warning (in development).

### Adapter Integration
Hugging Face's `from_pretrained` and `pipeline` methods accept a `revision` parameter. By supplying our verified SHA to this parameter, the `huggingface_hub` library natively verifies the model's signature (commit hash) against the server and downloads only the specified, immutable version.

- **Example Usage in Adapters:**
```python
from core.utils.model_security import get_verified_revision

revision = get_verified_revision("cvssp/audioldm-s-full-v2")
self.pipe = AudioLDMPipeline.from_pretrained(
    "cvssp/audioldm-s-full-v2", 
    revision=revision,
    torch_dtype=torch.float16
)
```

## 3. Scope of Implementation

For this phase, we will secure the primary inference adapters:
1. `AudioMixin` (XTTS, AudioLDM, Moshi)
2. `LocalTextAdapter` (LLMs)
3. `ImageGenMixin` (Diffusers/Stable Diffusion)
4. `VlmMixin` / `Qwen3VLAdapter` (Vision Language Models)

*Pipelines and scripts (MLOps) can be retrofitted in a subsequent pass.*

## 4. Success Criteria
- [ ] `model_security.py` contains a registry with real SHAs for core models.
- [ ] At least 3 core adapters are updated to pass the `revision` parameter.
- [ ] Tests verify that unverified models are blocked in strict mode.

## 5. Security Check
- **Integrity:** Passing a SHA-1 hash to `revision` guarantees bit-for-bit identical downloads across environments.
- **Cache:** This ensures the local HF cache isn't poisoned by a newer, malicious commit on the `main` branch.
