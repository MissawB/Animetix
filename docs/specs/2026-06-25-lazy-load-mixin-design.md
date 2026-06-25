# Design — LazyLoadMixin (dedup multi-submodel lazy loaders)

**Date:** 2026-06-25
**Status:** Approved
**TODO source:** "Backend — duplication entre adapters d'inférence" → "Reste : factoriser le motif `_load_model()` (try/except + cache lazy) … des adapters de modèles **locaux**." ([TODO.md](../../TODO.md))
**Predecessor:** [2026-06-23-lazy-local-model-adapter-base-design.md](2026-06-23-lazy-local-model-adapter-base-design.md) (the *single*-model base + readiness `health_check`, already merged).

## Problem

The single-model lazy-load wrapper and the readiness `health_check` were already factored into
`LazyLocalModelAdapter`, and every model-holding local adapter is migrated onto it. What remains is
the **multi-submodel** lazy-load duplication that the single-model base can't absorb:

- `ImageGenMixin._load_txt2img` / `_load_img2img` / `_load_inpainting`
- `AudioMixin._load_xtts` / `_load_audioldm` / `_load_moshi`

Each of these six methods repeats the same control flow:

1. a CUDA precondition that **raises** `InferenceError` when no GPU is present,
2. an idempotent guard (`if hasattr(self, attr) and <attr>: return`),
3. `try: <load into self.<attr>> except Exception as e: logger.error("❌ Failed to load …: {e}")`
   — i.e. the load failure is **swallowed** (logged, not re-raised).

The load *body* differs per sub-model; the guard + the try/except/log wrapper are duplicated.

## Current state (verified)

- `LazyLocalModelAdapter._load_model` is the single-model wrapper: guard `if self._is_loaded()` then
  `try: self._load_model_impl() except Exception: log + raise InferenceError(...)`. Its policy is
  **re-raise**.
- `ImageGenMixin` is a plain `class ImageGenMixin:` (no base). Its three loaders swallow load errors.
  Used by `DiffusersAdapter(ImageGenMixin, LazyLocalModelAdapter)` **and**
  `UnifiedInferenceAdapter(…, ImageGenMixin, …, InferencePort)` — the latter does **not** extend
  `LazyLocalModelAdapter`.
- `AudioMixin` is a plain class; its three loaders swallow load errors and emit a `logger.warning`
  before the CUDA `raise`. Used by `AudioTransformersAdapter(AudioMixin, LazyLocalModelAdapter)` and
  `UnifiedInferenceAdapter`.
- The CUDA check sits **before** the guard in all six methods (so a missing GPU raises even if the
  sub-model were already loaded — an order we preserve).

## Goals / non-goals

**Goals**
1. A small, unit-testable `LazyLoadMixin` owning the idempotent guard + try/except/log wrapper, with
   a selectable error policy (`swallow` default, `raise` to wrap in `InferenceError`).
2. `ImageGenMixin` and `AudioMixin` migrated onto it; the six loaders reduced to a precondition + a
   one-line `_lazy_load(...)` call + a verbatim `_build_*` body. Observable behavior identical.

**Non-goals**
- `RerankMixin`'s inline load (tangled inside a shared try with `.predict()` and a prompt-based
  fallback) — factoring risks the fallback path. Left as-is.
- `LocalTextAdapter.get_text_embedding`'s inline embedding load (currently **no** try/except — a
  failure propagates raw; a guard+try/except helper would change that). Left as-is.
- `LocalGuardrailAdapter` (holds no model; facade over an injected engine). Left as-is.
- Reworking `LazyLocalModelAdapter` (its `_load_model` already is the `raise`-policy shape).

## Design

### 1. The mixin

`backend/adapters/inference/lazy_load_mixin.py`:

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

`getattr(self, attr, None)` is equivalent to the existing `hasattr(self, attr) and <attr>` guard.

### 2. ImageGenMixin

- `class ImageGenMixin(LazyLoadMixin):`
- Each loader keeps its CUDA precondition inline (before the guard), then delegates:

```python
def _load_txt2img(self):
    if not torch.cuda.is_available():
        raise InferenceError("CUDA GPU is not available for local diffusion.")
    self._lazy_load("pipe", self._build_txt2img, label="txt2img")

def _build_txt2img(self):
    from diffusers import AutoPipelineForText2Image  # noqa: E402
    model_id = getattr(self, "model_id", "black-forest-labs/FLUX.1-schnell")
    logger.info(f"🏗️ Loading Txt2Img: {model_id}")
    self.pipe = AutoPipelineForText2Image.from_pretrained(...)
    self.pipe.to("cuda")
    self.pipe.enable_model_cpu_offload()
    self.pipe.enable_vae_tiling()
```

The `_build_*` body is the **current `try:` body, moved verbatim** (it still assigns `self.pipe`
first, then configures it — so the partial-cache-on-config-failure semantics are unchanged).
`_load_img2img`→`_build_img2img` (`_img2img_pipe`) and `_load_inpainting`→`_build_inpainting`
(`_inpaint_pipe`) identically. `on_error` defaults to `swallow` — matching today.

### 3. AudioMixin

- `class AudioMixin(LazyLoadMixin):`
- Same treatment for `_load_xtts` (`_tts_model`), `_load_audioldm` (`_audioldm_pipeline`),
  `_load_moshi` (`_moshi_model`). The CUDA `logger.warning(...)` + `raise InferenceError(...)` block
  stays inline verbatim before the `_lazy_load` call. `_build_*` bodies are the current `try:` bodies
  moved verbatim.

### 4. MRO

`DiffusersAdapter(ImageGenMixin, LazyLocalModelAdapter)` →
`… ImageGenMixin, LazyLoadMixin, LazyLocalModelAdapter, InferencePort, object` — fine.
`UnifiedInferenceAdapter(…, AudioMixin, ImageGenMixin, …, InferencePort)` picks up `LazyLoadMixin`
once via both mixins; C3 linearization collapses the shared single base — no diamond conflict. Both
expose `self._lazy_load`.

## Behavior preservation

- Guard semantics: `getattr(...) is truthy` ≡ `hasattr and truthy`.
- CUDA precondition order, messages, and the audio warning log: unchanged (kept inline).
- Error policy: `swallow` for all six (identical to today); the failure log text is the same
  `❌ Failed to load {label}` form.
- `_build_*` bodies are byte-for-byte the old `try:` bodies, so caching/partial-state behavior on a
  mid-load failure is identical.

No public behavior changes. No test should need updating except additions.

## Testing (TDD)

- **New** `tests/adapters/inference/test_lazy_load_mixin.py` against a minimal concrete subclass:
  - no-op when `attr` already truthy (loader not called),
  - calls `loader` when not loaded,
  - a raising loader under `on_error="swallow"` logs and does **not** raise; attr stays falsy,
  - a raising loader under `on_error="raise"` raises `InferenceError` with `label` in the message,
  - `label` appears in the error log.
- **Regression gate:** existing `tests/adapters/test_diffusers_adapter.py`,
  `tests/core/test_diffusers_adapter.py`, `tests/adapters/test_cuda_guard_fallbacks.py`, and any
  audio/unified adapter suites stay green unchanged.
- All loads are mocked (no GPU / HF download) — CI-safe.

## Risks / mitigations

- **Risk:** `on_error="raise"` is unused by any caller (YAGNI). *Mitigation:* it documents the base's
  policy in one place and is unit-tested; drop it only if review prefers. *(Confirmed kept.)*
- **Risk:** MRO regression from adding a base to the mixins. *Mitigation:* the full adapter suite is
  the gate; the single shared base linearizes cleanly.
- **Risk:** a `_build_*` body subtly diverges from the original on copy. *Mitigation:* move verbatim;
  diff each against the prior `try:` body.

## Out of scope / follow-up

- `RerankMixin` inline load and `LocalText.get_text_embedding` inline load (behavior-change risk).
- `LocalGuardrailAdapter` (no model). After this lands, the local-model dedup TODO can be closed with
  a note that these three are intentionally left.
