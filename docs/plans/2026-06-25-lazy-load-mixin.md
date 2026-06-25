# LazyLoadMixin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Factor the duplicated guard + try/except/log lazy-load wrapper out of `ImageGenMixin` and `AudioMixin` into a shared, tested `LazyLoadMixin`, behavior-preservingly.

**Architecture:** A new `LazyLoadMixin` provides one method `_lazy_load(attr, loader, *, label, on_error="swallow")` — idempotent guard, run loader, log on failure, swallow (default) or wrap-and-raise. `ImageGenMixin` and `AudioMixin` inherit it; each of their six `_load_*` methods keeps its CUDA precondition inline, then delegates to `_lazy_load`, with the original load body moved verbatim into a `_build_*` callable.

**Tech Stack:** Python, pytest. Models loaded via `transformers`/`diffusers`/`TTS`/`moshi` (all mocked in tests; no GPU/network).

**Spec:** [docs/specs/2026-06-25-lazy-load-mixin-design.md](../specs/2026-06-25-lazy-load-mixin-design.md)

## Global Constraints

- Behavior-preserving refactor: no public behavior change. `_build_*` bodies are the prior `try:` bodies moved **verbatim** (same attribute-assignment order).
- CUDA precondition stays **inline, before** the `_lazy_load` call (preserves raise-before-guard order). Error/warning message text unchanged.
- Error policy for all six loaders is `swallow` (the default) — identical to today.
- `label` values must equal the current error-log subject so `❌ Failed to load {label}` text is unchanged: `txt2img`, `img2img`, `inpainting`, `XTTS`, `AudioLDM`, `Moshi`.
- Tests mock all model loads — CI-safe (no GPU, no HF download).
- Run all commands from the worktree root: `C:\Users\bahma\PycharmProjects\Projet solo\Double_scenario_Project\.claude\worktrees\refactor-api-reachability-mixin`. Tests run with `python -m pytest`.

---

### Task 1: LazyLoadMixin (new module + unit tests)

**Files:**
- Create: `backend/adapters/inference/lazy_load_mixin.py`
- Test: `tests/adapters/inference/test_lazy_load_mixin.py`

**Interfaces:**
- Consumes: `core.domain.exceptions.InferenceError`.
- Produces: `class LazyLoadMixin` with `_lazy_load(self, attr: str, loader: Callable[[], Any], *, label: str, on_error: str = "swallow") -> None`. Idempotent when `getattr(self, attr, None)` is truthy; runs `loader()` otherwise; on exception logs `❌ Failed to load {label}: {e}` then swallows (`on_error="swallow"`) or raises `InferenceError(f"Critical failure during {label} model loading: {e}")` (`on_error="raise"`).

- [ ] **Step 1: Write the failing test**

Create `tests/adapters/inference/test_lazy_load_mixin.py`:

```python
import logging

import pytest
from adapters.inference.lazy_load_mixin import LazyLoadMixin
from core.domain.exceptions import InferenceError


class _Fake(LazyLoadMixin):
    def __init__(self):
        self.attr = None
        self._loads = 0

    def _good(self):
        self._loads += 1
        self.attr = object()

    def _bad(self):
        self._loads += 1
        raise RuntimeError("boom")


def test_lazy_load_calls_loader_when_not_loaded():
    f = _Fake()
    f._lazy_load("attr", f._good, label="thing")
    assert f._loads == 1 and f.attr is not None


def test_lazy_load_noop_when_already_loaded():
    f = _Fake()
    f.attr = object()
    f._lazy_load("attr", f._good, label="thing")
    assert f._loads == 0


def test_lazy_load_swallows_failure_by_default(caplog):
    f = _Fake()
    with caplog.at_level(logging.ERROR):
        f._lazy_load("attr", f._bad, label="thing")  # must NOT raise
    assert f.attr is None  # stays unset so a retry is possible
    assert "Failed to load thing" in caplog.text


def test_lazy_load_raises_when_on_error_raise():
    f = _Fake()
    with pytest.raises(
        InferenceError, match="Critical failure during thing model loading: boom"
    ):
        f._lazy_load("attr", f._bad, label="thing", on_error="raise")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/adapters/inference/test_lazy_load_mixin.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'adapters.inference.lazy_load_mixin'`.

- [ ] **Step 3: Write minimal implementation**

Create `backend/adapters/inference/lazy_load_mixin.py`:

```python
import logging
from typing import Any, Callable

from core.domain.exceptions import InferenceError

logger = logging.getLogger("animetix.inference.lazy_load")


class LazyLoadMixin:
    """Idempotent best-effort lazy-load helper for adapters/mixins that load
    several sub-models on demand (each into its own attribute).

    ``_lazy_load`` is a no-op when ``attr`` is already truthy; otherwise it runs
    ``loader`` (which sets ``self.<attr>``). On failure it logs and, by policy,
    either swallows (default) or wraps the error in ``InferenceError``.
    """

    def _lazy_load(
        self,
        attr: str,
        loader: Callable[[], Any],
        *,
        label: str,
        on_error: str = "swallow",
    ) -> None:
        if getattr(self, attr, None):
            return
        try:
            loader()
        except Exception as e:
            logger.error(f"❌ Failed to load {label}: {e}")
            if on_error == "raise":
                raise InferenceError(
                    f"Critical failure during {label} model loading: {e}"
                )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/adapters/inference/test_lazy_load_mixin.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/adapters/inference/lazy_load_mixin.py tests/adapters/inference/test_lazy_load_mixin.py
git commit -m "feat(inference): add LazyLoadMixin (idempotent best-effort lazy loader)"
```

---

### Task 2: Migrate ImageGenMixin onto LazyLoadMixin

**Files:**
- Modify: `backend/adapters/inference/image_gen_mixin.py` (class decl line 50; loaders lines 70-135)
- Regression test (no edit): `tests/adapters/test_diffusers_adapter.py`, `tests/core/test_diffusers_adapter.py`, `tests/adapters/test_cuda_guard_fallbacks.py`, `tests/adapters/test_adapter_health_check.py`

**Interfaces:**
- Consumes: `LazyLoadMixin._lazy_load` from Task 1.
- Produces: `ImageGenMixin(LazyLoadMixin)` with unchanged public methods `_load_txt2img`/`_load_img2img`/`_load_inpainting`; new private `_build_txt2img`/`_build_img2img`/`_build_inpainting` setting `self.pipe`/`self._img2img_pipe`/`self._inpaint_pipe`.

- [ ] **Step 1: Run the existing regression tests first (baseline GREEN)**

Run: `python -m pytest tests/adapters/test_diffusers_adapter.py tests/core/test_diffusers_adapter.py tests/adapters/test_cuda_guard_fallbacks.py -q`
Expected: PASS. Record the count; it must not drop after the edit.

- [ ] **Step 2: Add the import and base class**

In `backend/adapters/inference/image_gen_mixin.py`, add the import after the existing `core.utils` imports (near line 14):

```python
from adapters.inference.lazy_load_mixin import LazyLoadMixin  # noqa: E402
```

Change the class declaration (line 50) from:

```python
class ImageGenMixin:
```
to:
```python
class ImageGenMixin(LazyLoadMixin):
```

- [ ] **Step 3: Replace the three loaders with precondition + delegate + verbatim `_build_*`**

Replace the whole block of `_load_txt2img` / `_load_img2img` / `_load_inpainting` (lines 70-135) with:

```python
    def _load_txt2img(self):
        if not torch.cuda.is_available():
            raise InferenceError("CUDA GPU is not available for local diffusion.")
        self._lazy_load("pipe", self._build_txt2img, label="txt2img")

    def _build_txt2img(self):
        from diffusers import AutoPipelineForText2Image  # noqa: E402

        model_id = getattr(self, "model_id", "black-forest-labs/FLUX.1-schnell")
        logger.info(f"🏗️ Loading Txt2Img: {model_id}")
        self.pipe = AutoPipelineForText2Image.from_pretrained(
            model_id,
            torch_dtype=self._get_dtype(),
            variant=self._get_variant(),
            trust_remote_code=resolve_trust_remote_code(model_id),
            revision=trusted_revision(model_id) or "main",
        )
        self.pipe.to("cuda")
        self.pipe.enable_model_cpu_offload()
        self.pipe.enable_vae_tiling()

    def _load_img2img(self):
        if not torch.cuda.is_available():
            raise InferenceError("CUDA GPU is not available for local diffusion.")
        self._lazy_load("_img2img_pipe", self._build_img2img, label="img2img")

    def _build_img2img(self):
        from diffusers import AutoPipelineForImage2Image  # noqa: E402

        model_id = getattr(self, "model_id", "black-forest-labs/FLUX.1-schnell")
        logger.info(f"🏗️ Loading Img2Img: {model_id}")
        self._img2img_pipe = AutoPipelineForImage2Image.from_pretrained(
            model_id,
            torch_dtype=self._get_dtype(),
            variant=self._get_variant(),
            trust_remote_code=resolve_trust_remote_code(model_id),
            revision=trusted_revision(model_id) or "main",
        )
        self._img2img_pipe.to("cuda")
        self._img2img_pipe.enable_model_cpu_offload()

    def _load_inpainting(self):
        if not torch.cuda.is_available():
            raise InferenceError("CUDA GPU is not available for local diffusion.")
        self._lazy_load("_inpaint_pipe", self._build_inpainting, label="inpainting")

    def _build_inpainting(self):
        from diffusers import AutoPipelineForInpainting  # noqa: E402

        model_id = getattr(self, "model_id", "black-forest-labs/FLUX.1-schnell")
        logger.info(f"🏗️ Loading Inpainting: {model_id}")
        self._inpaint_pipe = AutoPipelineForInpainting.from_pretrained(
            model_id,
            torch_dtype=self._get_dtype(),
            variant=self._get_variant(),
            trust_remote_code=resolve_trust_remote_code(model_id),
            revision=trusted_revision(model_id) or "main",
        )
        self._inpaint_pipe.to("cuda")
        self._inpaint_pipe.enable_model_cpu_offload()
```

- [ ] **Step 4: Run regression tests to verify still GREEN**

Run: `python -m pytest tests/adapters/test_diffusers_adapter.py tests/core/test_diffusers_adapter.py tests/adapters/test_cuda_guard_fallbacks.py tests/adapters/test_adapter_health_check.py -q`
Expected: PASS, same count as Step 1 (no regressions).

- [ ] **Step 5: Lint**

Run: `python -m ruff check backend/adapters/inference/image_gen_mixin.py && python -m ruff format --check backend/adapters/inference/image_gen_mixin.py`
Expected: `All checks passed!` and `1 file already formatted`. If format check fails, run `python -m ruff format backend/adapters/inference/image_gen_mixin.py` and re-run Step 4.

- [ ] **Step 6: Commit**

```bash
git add backend/adapters/inference/image_gen_mixin.py
git commit -m "refactor(inference): route ImageGenMixin loaders through LazyLoadMixin"
```

---

### Task 3: Migrate AudioMixin onto LazyLoadMixin

**Files:**
- Modify: `backend/adapters/inference/audio_mixin.py` (class decl line 21; loaders lines 40-119)
- Regression test (no edit): `tests/adapters/test_unified_inference_adapter.py`, `tests/adapters/test_adapter_health_check.py`, any audio adapter suite

**Interfaces:**
- Consumes: `LazyLoadMixin._lazy_load` from Task 1.
- Produces: `AudioMixin(LazyLoadMixin)` with unchanged public methods `_load_xtts`/`_load_audioldm`/`_load_moshi`; new private `_build_xtts`/`_build_audioldm`/`_build_moshi` setting `self._tts_model`/`self._audioldm_pipeline`/`self._moshi_model`.

- [ ] **Step 1: Run the existing regression tests first (baseline GREEN)**

Run: `python -m pytest tests/adapters/test_unified_inference_adapter.py tests/adapters/test_adapter_health_check.py -q`
Expected: PASS. Record the count.

- [ ] **Step 2: Add the import and base class**

In `backend/adapters/inference/audio_mixin.py`, add after the existing `core.utils` imports (near line 13):

```python
from adapters.inference.lazy_load_mixin import LazyLoadMixin  # noqa: E402
```

Change the class declaration (line 21) from:

```python
class AudioMixin:
```
to:
```python
class AudioMixin(LazyLoadMixin):
```

- [ ] **Step 3: Replace the three loaders with precondition + delegate + verbatim `_build_*`**

Replace the whole block of `_load_xtts` / `_load_audioldm` / `_load_moshi` (lines 40-119) with:

```python
    def _load_xtts(self):
        if not torch.cuda.is_available():
            logger.warning(
                "⚠️ GPU CUDA non détecté. Chargement local des modèles audio désactivé."
            )
            raise InferenceError(
                "CUDA GPU is not available. Local audio models loading is disabled."
            )
        self._lazy_load("_tts_model", self._build_xtts, label="XTTS")

    def _build_xtts(self):
        from TTS.api import TTS  # noqa: E402

        # Check for mounted local volume
        mount_path = os.getenv("GCP_MODELS_MOUNT_PATH", "/mnt/models")
        local_model_path = os.path.join(mount_path, "xtts_v2")
        if os.path.exists(local_model_path):
            logger.info(
                f"🎙️ Loading XTTS Model from local FUSE path: {local_model_path}"
            )
            self._tts_model = TTS(model_path=local_model_path)
        else:
            model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
            logger.info(f"🎙️ Loading XTTS Model from Hugging Face: {model_name}")
            self._tts_model = TTS(model_name)

        if torch.cuda.is_available():
            self._tts_model.to("cuda")

    def _load_audioldm(self):
        if not torch.cuda.is_available():
            logger.warning(
                "⚠️ GPU CUDA non détecté. Chargement local des modèles audio désactivé."
            )
            raise InferenceError(
                "CUDA GPU is not available. Local audio models loading is disabled."
            )
        self._lazy_load("_audioldm_pipeline", self._build_audioldm, label="AudioLDM")

    def _build_audioldm(self):
        from diffusers import AudioLDMPipeline  # noqa: E402

        logger.info("🎧 Loading AudioLDM for Soundscapes...")
        model_id = "cvssp/audioldm-s-full-v2"
        revision = get_verified_revision(model_id)
        self._audioldm_pipeline = AudioLDMPipeline.from_pretrained(
            model_id,
            revision=revision,
            torch_dtype=(
                torch.float16 if torch.cuda.is_available() else torch.float32
            ),
        )
        if torch.cuda.is_available():
            self._audioldm_pipeline.to("cuda")

    def _load_moshi(self):
        if not torch.cuda.is_available():
            logger.warning(
                "⚠️ GPU CUDA non détecté. Chargement local des modèles audio désactivé."
            )
            raise InferenceError(
                "CUDA GPU is not available. Local audio models loading is disabled."
            )
        self._lazy_load("_moshi_model", self._build_moshi, label="Moshi")

    def _build_moshi(self):
        from moshi.models import Moshi  # noqa: E402

        logger.info("🗣️ Loading Kyutai Moshi (S2S)...")
        model_id = "kyutai/moshiko-pytorch-bf16"
        revision = get_verified_revision(model_id)
        self._moshi_model = Moshi.from_pretrained(model_id, revision=revision)
        if torch.cuda.is_available():
            self._moshi_model.to("cuda")
```

- [ ] **Step 4: Run regression tests to verify still GREEN**

Run: `python -m pytest tests/adapters/test_unified_inference_adapter.py tests/adapters/test_adapter_health_check.py -q`
Expected: PASS, same count as Step 1.

- [ ] **Step 5: Lint**

Run: `python -m ruff check backend/adapters/inference/audio_mixin.py && python -m ruff format --check backend/adapters/inference/audio_mixin.py`
Expected: `All checks passed!` and `1 file already formatted`. If format check fails, run `python -m ruff format backend/adapters/inference/audio_mixin.py` and re-run Step 4.

- [ ] **Step 6: Commit**

```bash
git add backend/adapters/inference/audio_mixin.py
git commit -m "refactor(inference): route AudioMixin loaders through LazyLoadMixin"
```

---

### Task 4: Full-suite gate + close the TODO

**Files:**
- Modify: `TODO.md` (line 25, the "Reste" bullet under "duplication entre adapters d'inférence")

**Interfaces:**
- Consumes: Tasks 1-3 complete.
- Produces: none (docs only).

- [ ] **Step 1: Run the whole adapter test suite as the final regression gate**

Run: `python -m pytest tests/adapters tests/core -q`
Expected: PASS (no failures, no new warnings attributable to this change).

- [ ] **Step 2: Update TODO.md**

In `TODO.md`, replace the line-25 bullet:

```markdown
  - ⏳ **Reste** : factoriser le motif `_load_model()` (try/except + cache lazy) et le `health_check` *readiness* des adapters de modèles **locaux**.
```
with:

```markdown
  - ✅ `health_check` *readiness* factorisé dans [LazyLocalModelAdapter](backend/adapters/inference/lazy_local_model_adapter.py) (tous les adapters à modèle local migrés) ; motif `_load_model()` multi-sous-modèles factorisé dans [LazyLoadMixin](backend/adapters/inference/lazy_load_mixin.py) (`ImageGenMixin`/`AudioMixin`).
  - ⏳ **Reste (résiduel, hors scope)** : `RerankMixin` et `LocalTextAdapter.get_text_embedding` (chargements inline aux sémantiques d'erreur différentes) ; `LocalGuardrailAdapter` (aucun modèle).
```

- [ ] **Step 3: Commit**

```bash
git add TODO.md
git commit -m "docs(todo): mark local-model lazy-load/health dedup done; note residuals"
```

---

## Self-Review

**Spec coverage:**
- LazyLoadMixin module + policy → Task 1. ✓
- ImageGenMixin migration (3 loaders, verbatim bodies, CUDA inline, swallow) → Task 2. ✓
- AudioMixin migration (3 loaders, warning+raise inline, swallow) → Task 3. ✓
- Non-goals (RerankMixin / embedding / LocalGuardrail / base untouched) → not in any task; noted in Task 4 TODO. ✓
- Tests: new unit tests (Task 1) + regression gates (Tasks 2-4). ✓
- MRO: exercised by the existing diffusers/unified adapter suites in Tasks 2-3 (those concrete classes compose the mixins). ✓

**Placeholder scan:** none — every code/edit step shows full content; labels and messages are literal.

**Type/name consistency:** `_lazy_load(attr, loader, *, label, on_error="swallow")` used identically in Tasks 2-3; `_build_*` names map 1:1 to attributes `pipe`/`_img2img_pipe`/`_inpaint_pipe`/`_tts_model`/`_audioldm_pipeline`/`_moshi_model`; labels `txt2img`/`img2img`/`inpainting`/`XTTS`/`AudioLDM`/`Moshi` match current error-log text.
