# Design — LazyLocalModelAdapter base (dedup inference adapters, pilot)

**Date:** 2026-06-23
**Status:** Approved (approach A; pilot)
**TODO source:** "Backend — duplication entre adapters d'inférence — `health_check()` and the lazy `_load_model()` (try/except + cache) reimplemented in each adapter → factor into a common base/mixin."

## Problem

Across `backend/adapters/inference/`, ~8 adapters reimplement an attribute-based `health_check`
(`{"status": "online" if <attr> else "offline", "engine": <name>}`) and two adapters
(`LocalTextAdapter`, `MoondreamAdapter`) reimplement a byte-identical lazy `_load_model` control
flow (`if self.model: return` → `try: <load>` → `except: log + raise InferenceError`). The load
*body* differs; the *wrapper* and the health dict are duplicated.

This is a **pilot**: introduce one common base, `LazyLocalModelAdapter`, that factors both the
lazy-load wrapper and the health dict, and migrate the two "local HF model" adapters
(`LocalTextAdapter`, `MoondreamAdapter`) onto it. `CompactReasoningAdapter` (which extends
`LocalTextAdapter`) benefits transitively with no change. The remaining attribute-health adapters
and other lazy-loads are follow-ups. Behavior-preserving.

## Current state (verified)

- `InferencePort.health_check` is `@abstractmethod` (no default); every adapter implements it.
- `LocalTextAdapter(InferencePort)`: `__init__` sets `self.model=None`, `self.tokenizer=None`,
  `self._embedding_model=None`, `self.draft_model=None`. `_load_model()` = `if self.model: return`
  then `try:` load tokenizer + model (+ optional draft) `except Exception as e: logger.error(...);
  raise InferenceError("Critical failure during text model loading: {e}")`. `health_check()` =
  `{"status": "online" if self.model or self._embedding_model else "offline", "engine":
  "local_text"}`. `get_text_embedding` lazily loads `self._embedding_model` inline (no try/except —
  out of scope here).
- `MoondreamAdapter(InferencePort)`: `__init__` sets `self.model=None`, `self.processor=None`.
  `_load_model()` = `if self.model: return` then `try:` load model + processor `except Exception
  as e: logger.error(...); raise InferenceError("SmolVLM loading failed: {e}")`. `health_check()` =
  `{"status": "online" if self.model else "offline", "engine": "SmolVLM"}`.
- `CompactReasoningAdapter(LocalTextAdapter)`: its `health_check` calls `super().health_check()`
  and adds `adapter`/`specialization` fields; it does not override `_load_model`.
- Tests: `tests/adapters/inference/test_local_text_adapter.py` has `test_health_check`
  (offline→online after load) and `test_get_text_embedding_lazy_loading`.

## Goals / non-goals

**Goals**
1. A `LazyLocalModelAdapter(InferencePort)` base owning the guarded lazy-load wrapper and the
   attribute-based `health_check`.
2. `LocalTextAdapter` and `MoondreamAdapter` migrated onto it with identical observable behavior
   (same `_load_model` guard/raise semantics, same `health_check` dicts).
3. The base is unit-testable in isolation.

**Non-goals**
- Migrating the other 6 attribute-health adapters or other lazy-loads (follow-ups).
- Wrapping `LocalTextAdapter.get_text_embedding`'s inline embedding load (would change behavior).
- Changing `CompactReasoningAdapter` (benefits transitively, untouched).

## Design (approach A)

### 1. Base class

`backend/adapters/inference/lazy_local_model_adapter.py`:

```python
import logging

from core.domain.exceptions import InferenceError
from core.ports.inference_port import InferencePort

logger = logging.getLogger("animetix.inference.lazy_local")


class LazyLocalModelAdapter(InferencePort):
    """Base for adapters that lazily load a local model.

    Subclasses set ``ENGINE_NAME`` and implement ``_load_model_impl`` (the actual,
    unguarded load). The base provides the guarded lazy-load wrapper and the
    attribute-based ``health_check``. ``_is_loaded`` is the lazy-load guard;
    ``_is_ready`` is the (possibly broader) health signal.
    """

    ENGINE_NAME: str = "local"

    def _load_model(self) -> None:
        if self._is_loaded():
            return
        try:
            self._load_model_impl()
        except Exception as e:
            logger.error(f"❌ Failed to load {self.ENGINE_NAME} model: {e}")
            raise InferenceError(
                f"Critical failure during {self.ENGINE_NAME} model loading: {e}"
            )

    def _is_loaded(self) -> bool:
        return getattr(self, "model", None) is not None

    def _load_model_impl(self) -> None:
        raise NotImplementedError

    def _is_ready(self) -> bool:
        return self._is_loaded()

    def health_check(self) -> dict:
        return {
            "status": "online" if self._is_ready() else "offline",
            "engine": self.ENGINE_NAME,
        }
```

The base does not override `__init__`, so `InferencePort.__init__(usage_port)` still applies. The
base remains abstract (it does not implement `generate`/`stream_generate`/`get_text_embedding`), so
it cannot be instantiated directly — only subclassed.

### 2. LocalTextAdapter

- `class LocalTextAdapter(LazyLocalModelAdapter)`; class attribute `ENGINE_NAME = "local_text"`.
- Remove the `_load_model` method (inherited from the base). Move its `try:` body (the tokenizer +
  model + optional draft-model loads) into `_load_model_impl(self)` — no guard, no try/except (the
  base supplies both).
- Remove `health_check`; override `_is_ready` to preserve the broader signal:
  `return self.model is not None or self._embedding_model is not None`.
- `get_text_embedding` is unchanged.

### 3. MoondreamAdapter

- `class MoondreamAdapter(LazyLocalModelAdapter)`; `ENGINE_NAME = "SmolVLM"`.
- Remove `_load_model`; move its `try:` body (model + processor loads) into `_load_model_impl`.
- Remove `health_check` (the base default `_is_ready == _is_loaded == self.model` matches exactly).

### 4. CompactReasoningAdapter — unchanged

It extends `LocalTextAdapter`, inherits the new `_load_model`/`_load_model_impl` and the overridden
`_is_ready`, and its own `health_check` still calls `super().health_check()` (now the base method,
`engine="local_text"`) then enriches it. Behavior identical; no edit.

## Behavior change note (accepted)

The base unifies the `InferenceError` message to `"Critical failure during {ENGINE_NAME} model
loading: {e}"` and the log line to `"❌ Failed to load {ENGINE_NAME} model: {e}"`. This changes the
exact *text* of Moondream's message (`"SmolVLM loading failed"` → `"Critical failure during SmolVLM
model loading"`); the *type* (`InferenceError`) and the raise-on-failure behavior are preserved. Any
test asserting the exact message text is updated; tests asserting the exception type are unaffected.

## Testing (TDD)

- **Base unit tests** (`tests/adapters/inference/test_lazy_local_model_adapter.py`): a minimal
  concrete subclass (sets `ENGINE_NAME`, a `model` attr, `_load_model_impl`) asserts: `_load_model`
  is a no-op when `_is_loaded()`; calls `_load_model_impl` when not loaded; a raising
  `_load_model_impl` is wrapped in `InferenceError`; `health_check` returns
  `online`/`offline`+`ENGINE_NAME` driven by `_is_ready`; a subclass overriding `_is_ready` changes
  the health result without affecting the lazy-load guard.
- **LocalTextAdapter / MoondreamAdapter:** the existing `test_local_text_adapter.py` tests
  (`test_health_check`, `test_get_text_embedding_lazy_loading`) and any Moondream tests stay green;
  update the single error-message assertion if one exists.
- The full `tests/adapters` suite is the regression gate.
- All tests mock the model loads (no live HF download / GPU) — CI-safe.

## Risks / mitigations

- **Risk:** `_is_ready` vs `_is_loaded` conflation drops LocalText's embedding-model health signal.
  *Mitigation:* LocalText overrides `_is_ready` explicitly; a base unit test proves the two hooks
  are independent.
- **Risk:** the error-message text change breaks a test. *Mitigation:* find-and-update the one
  assertion; the exception type is unchanged.
- **Risk:** MRO/`super().__init__` regressions. *Mitigation:* the base adds no `__init__`; the full
  adapter suite runs as the gate.

## Out of scope / follow-up

- Migrate the other attribute-health adapters (diffusers, rerank, audio, manga_ocr,
  local_guardrail, vision_transformers, google_genai) — likely via a `HealthCheckMixin` reusing
  `_is_ready`/`ENGINE_NAME`.
- Guard `get_text_embedding`'s inline embedding load.
