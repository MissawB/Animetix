# Dynamic CUDA GPU Detection & CPU Memory Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent local deep learning execution on CPU, raising a clear diagnostic `InferenceError` inside local adapters (Diffusers, AudioTransformers) when CUDA is unavailable, thereby triggering the cloud-based `BrainAPIAdapter` fallback smoothly without OOM crashes.

**Architecture:** We check `torch.cuda.is_available()` dynamically in `DiffusersAdapter` and `AudioTransformersAdapter` loading methods before initializing neural models. When CUDA is unavailable, we raise a diagnostic `InferenceError` exception. The orchestrator `FallbackInferenceAdapter` catches these and transitions to the remote fallback (`BrainAPIAdapter`) automatically. Manga bubble inpainting falls back locally to CPU-safe Pillow rendering.

**Tech Stack:** Python, PyTorch (`torch`), Diffusers, Transformers, Pytest.

---

### Task 1: Add CUDA Dynamic Check Guards to `DiffusersAdapter`

**Files:**
- Modify: `backend/adapters/inference/diffusers_adapter.py`
- Test: `tests/core/test_diffusers_adapter.py`

- [ ] **Step 1: Modify loading methods in `DiffusersAdapter` to perform dynamic CUDA checks**

Add `not torch.cuda.is_available()` check at the beginning of `_load_txt2img`, `_load_img2img`, and `_load_inpainting`. Raise `InferenceError` with a clear message and log a warning.

```python
# Insert at the beginning of _load_txt2img in diffusers_adapter.py
        if not torch.cuda.is_available():
            logger.warning("⚠️ GPU CUDA non détecté. Chargement local du modèle SDXL désactivé pour éviter un crash CPU/OOM.")
            raise InferenceError("CUDA GPU is not available. Local SDXL loading is disabled to prevent CPU memory crash.")
```

And similarly for `_load_img2img` and `_load_inpainting`:

```python
# Insert at the beginning of _load_img2img in diffusers_adapter.py
        if not torch.cuda.is_available():
            logger.warning("⚠️ GPU CUDA non détecté. Chargement local du modèle SDXL désactivé pour éviter un crash CPU/OOM.")
            raise InferenceError("CUDA GPU is not available. Local SDXL loading is disabled to prevent CPU memory crash.")
```

```python
# Insert at the beginning of _load_inpainting in diffusers_adapter.py
        if not torch.cuda.is_available():
            logger.warning("⚠️ GPU CUDA non détecté. Chargement local du modèle SDXL d'inpainting désactivé pour éviter un crash CPU/OOM.")
            raise InferenceError("CUDA GPU is not available. Local SDXL inpainting is disabled to prevent CPU memory crash.")
```

- [ ] **Step 2: Ensure existing `DiffusersAdapter` tests mock CUDA availability to return `True`**

Update `tests/core/test_diffusers_adapter.py` to patch `torch.cuda.is_available` to return `True` so they do not fail on machines without CUDA.

```python
# In tests/core/test_diffusers_adapter.py:
@pytest.fixture(autouse=True)
def mock_cuda_available():
    with patch("torch.cuda.is_available", return_value=True):
        yield
```

- [ ] **Step 3: Run existing tests to verify they pass**

Run: `.venv\Scripts\python -m pytest tests/core/test_diffusers_adapter.py -v`
Expected: PASS

- [ ] **Step 4: Commit the changes**

```bash
git add backend/adapters/inference/diffusers_adapter.py tests/core/test_diffusers_adapter.py
git commit -m "feat: add dynamic CUDA check guards to DiffusersAdapter"
```

---

### Task 2: Add CUDA Dynamic Check Guards to `AudioTransformersAdapter`

**Files:**
- Modify: `backend/adapters/inference/audio_transformers_adapter.py`
- Test: `tests/adapters/test_s2s_inference.py`

- [ ] **Step 1: Modify loading methods in `AudioTransformersAdapter` to perform dynamic CUDA checks**

Add `not torch.cuda.is_available()` check at the beginning of `_load_xtts`, `_load_audioldm`, and `_load_moshi`. Raise `InferenceError` with a clear message and log a warning.

```python
# Insert at the beginning of _load_xtts in audio_transformers_adapter.py
        if not torch.cuda.is_available():
            logger.warning("⚠️ GPU CUDA non détecté. Chargement local des modèles audio désactivé pour éviter une surcharge CPU/OOM.")
            raise InferenceError("CUDA GPU is not available. Local audio models loading is disabled.")
```

And similarly for `_load_audioldm` and `_load_moshi`:

```python
# Insert at the beginning of _load_audioldm in audio_transformers_adapter.py
        if not torch.cuda.is_available():
            logger.warning("⚠️ GPU CUDA non détecté. Chargement local des modèles audio désactivé pour éviter une surcharge CPU/OOM.")
            raise InferenceError("CUDA GPU is not available. Local audio models loading is disabled.")
```

```python
# Insert at the beginning of _load_moshi in audio_transformers_adapter.py
        if not torch.cuda.is_available():
            logger.warning("⚠️ GPU CUDA non détecté. Chargement local des modèles audio désactivé pour éviter une surcharge CPU/OOM.")
            raise InferenceError("CUDA GPU is not available. Local audio models loading is disabled.")
```

- [ ] **Step 2: Ensure existing `AudioTransformersAdapter` tests mock CUDA availability to return `True`**

Update `tests/adapters/test_s2s_inference.py` (or other relevant tests) to mock `torch.cuda.is_available` to return `True`.

```python
# In tests/adapters/test_s2s_inference.py (or via pytest fixture):
@pytest.fixture(autouse=True)
def mock_cuda_available():
    with patch("torch.cuda.is_available", return_value=True):
        yield
```

- [ ] **Step 3: Run existing tests to verify they pass**

Run: `.venv\Scripts\python -m pytest tests/adapters/test_s2s_inference.py -v`
Expected: PASS

- [ ] **Step 4: Commit the changes**

```bash
git add backend/adapters/inference/audio_transformers_adapter.py tests/adapters/test_s2s_inference.py
git commit -m "feat: add dynamic CUDA check guards to AudioTransformersAdapter"
```

---

### Task 3: Create Explicit Integration Tests for CUDA Fail-Fast & Orchestrator Fallback

**Files:**
- Create: `tests/adapters/test_cuda_guard_fallbacks.py`

- [ ] **Step 1: Write integration tests verifying fallback behaviors when CUDA is not available**

Create `tests/adapters/test_cuda_guard_fallbacks.py` containing:
1. A test verifying that `DiffusersAdapter` loading raises `InferenceError` when `torch.cuda.is_available` is mocked to `False`.
2. A test verifying that `AudioTransformersAdapter` loading raises `InferenceError` when `torch.cuda.is_available` is mocked to `False`.
3. A test verifying that `inpaint_text_bubbles` gracefully switches to Pillow-only local rendering (returns valid image base64, doesn't throw) when `torch.cuda.is_available` is mocked to `False`.
4. A test verifying that the global `FallbackInferenceAdapter` successfully catches the loading errors and falls back to `BrainAPIAdapter`.

```python
import pytest
from unittest.mock import MagicMock, patch
from core.domain.exceptions import InferenceError
from adapters.inference.diffusers_adapter import DiffusersAdapter
from adapters.inference.audio_transformers_adapter import AudioTransformersAdapter
from adapters.inference.fallback_adapter import FallbackInferenceAdapter
from adapters.inference.brain_api_adapter import BrainAPIAdapter

def test_diffusers_no_cuda_raises():
    adapter = DiffusersAdapter()
    with patch("torch.cuda.is_available", return_value=False):
        with pytest.raises(InferenceError) as exc_info:
            adapter.generate_image("prompt")
        assert "CUDA GPU is not available" in str(exc_info.value)

def test_audio_no_cuda_raises():
    adapter = AudioTransformersAdapter()
    with patch("torch.cuda.is_available", return_value=False):
        with pytest.raises(InferenceError) as exc_info:
            adapter.clone_voice("text", b"audio")
        assert "CUDA GPU is not available" in str(exc_info.value)

def test_diffusers_inpaint_pillow_fallback_on_no_cuda():
    adapter = DiffusersAdapter()
    # Mock Pillow Image rendering
    with patch("torch.cuda.is_available", return_value=False):
        res = adapter.inpaint_text_bubbles(b"dummy_image", [{"bbox": [0,0,10,10], "text": "Hello"}])
        assert res.startswith("data:image/jpeg;base64,")

def test_fallback_adapter_transitions_on_no_cuda():
    mock_brain = MagicMock(spec=BrainAPIAdapter)
    mock_brain.generate_image.return_value = "data:image/jpeg;base64,cloud_image"
    mock_diffusers = DiffusersAdapter()
    
    fallback = FallbackInferenceAdapter(adapters=[mock_brain, mock_diffusers])
    
    with patch("torch.cuda.is_available", return_value=False):
        res = fallback.generate_image("prompt")
        assert res == "data:image/jpeg;base64,cloud_image"
```

- [ ] **Step 2: Run the new fallback tests**

Run: `.venv\Scripts\python -m pytest tests/adapters/test_cuda_guard_fallbacks.py -v`
Expected: PASS

- [ ] **Step 3: Commit the new test file**

```bash
git add tests/adapters/test_cuda_guard_fallbacks.py
git commit -m "test: add CUDA fail-fast and fallback orchestrator integration tests"
```

---

### Task 4: Run the Complete Test Suite

- [ ] **Step 1: Execute all core and adapter tests to make sure no regressions occur**

Run: `.venv\Scripts\python -m pytest tests/core/ test_fallback_adapter.py tests/adapters/ -v`
Expected: PASS

---

### Task 5: Documentation Update

**Files:**
- Modify: `docs/TODO.md`
- Modify: `docs/HISTORY.md`

- [ ] **Step 1: Update `docs/TODO.md`**

Check off the CUDA GPU detection task:
```markdown
- [x] **Dégradation élégante (Inférence de Modèles Lourds)** : Détecter dynamiquement la présence de GPU CUDA dans `DiffusersAdapter` et `AudioTransformersAdapter`, et lever des alertes claires (ou fallbacks cloud) au lieu de crashs de mémoire/chargement en cas d'absence de GPU.
```

- [ ] **Step 2: Update `docs/HISTORY.md`**

Add the newly completed technical achievement in the "2026 - Restructuration Majeure" section.

```markdown
- **CUDA Dynamic GPU check & CPU Memory Guard :** Implémentation d'une détection proactive et dynamique des GPU CUDA (`torch.cuda.is_available()`) dans `DiffusersAdapter` et `AudioTransformersAdapter` empêchant tout chargement de modèles neuronaux lourds (SDXL, XTTS, Moshi, AudioLDM) sur CPU, évitant ainsi les ralentissements excessifs et les crashs par épuisement de mémoire (OOM). Les exceptions `InferenceError` levées sont automatiquement interceptées par l'orchestrateur global pour basculer sur le cloud distant (`BrainAPIAdapter`) de manière transparente.
```

- [ ] **Step 3: Commit the documentation updates**

```bash
git add docs/TODO.md docs/HISTORY.md
git commit -m "docs: document CUDA dynamic GPU detection and CPU memory guard"
```
