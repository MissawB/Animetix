# Design — UnifiedInferenceAdapter: mixins → composition (pilot)

**Date:** 2026-06-23
**Status:** Approved (approach A; pilot scope)
**TODO source:** "Backend — `UnifiedInferenceAdapter` god object — 8 mixins, MRO fragile, hard to test → composition over multiple inheritance"

## Problem

`UnifiedInferenceAdapter` (`backend/adapters/inference/unified_inference_adapter.py`) is assembled
by multiple-inheriting 8 mixins (`ClipVisionMixin`, `DepthEstimationMixin`, `MangaOcrMixin`,
`VideoAnalysisMixin`, `AudioMixin`, `ImageGenMixin`, `VlmMixin`, `RerankMixin`) plus
`InferencePort`. The MRO is fragile, the mixins share mutable state on `self` (lazy model caches,
`_log_usage`, `_last_completion/_logprobs`) and have hidden cross-mixin calls
(`VideoAnalysisMixin`→`ClipVisionMixin._load_clip_model/_clip_model`, `RerankMixin`→`self.generate`),
and the mixins cannot be unit-tested without constructing the whole adapter.

This is a **pilot**: convert exactly two mixins (`MangaOcrMixin`, `RerankMixin`) to a composition
pattern that establishes a reusable template for the remaining six (left in the TODO). It is a
**behavior-preserving** refactor — no functional change.

## Hard constraint (discovered)

`FallbackInferenceAdapter._is_method_overridden` (`backend/adapters/inference/fallback_adapter.py`)
decides whether an adapter "has" a capability by inspecting the **class**:
`getattr(adapter.__class__, method_name)` and comparing it by identity to `InferencePort`'s
version. `_build_capability_cache` iterates every public `InferencePort` method this way.

Consequence: any capability the fallback must route to `UnifiedInferenceAdapter` MUST be a method
**defined on the `UnifiedInferenceAdapter` class** and distinct from the `InferencePort` default.
Moving logic into composed objects therefore requires **thin delegating methods on the class**.
A `__getattr__`-based delegation would silently break routing (class-level `getattr` does not see
instance-resolved attributes) and is rejected.

## Goals / non-goals

**Goals**
1. Replace the `MangaOcrMixin` and `RerankMixin` inheritance with composed component classes that
   carry their own lazy state and receive their cross-cutting collaborators explicitly.
2. Keep `UnifiedInferenceAdapter`'s observable behavior and public interface identical, including
   capability detection by the fallback.
3. Make the two components unit-testable in isolation (no adapter, no HTTP, no real models/GPU).
4. Establish a documented template for migrating the remaining six mixins later.

**Non-goals**
- Converting the other six mixins (stay in the TODO).
- Fixing the pre-existing latent bug in `RerankMixin`'s prompt fallback (see below) — preserved.
- Changing `FallbackInferenceAdapter`, `InferencePort`, or any behavior.

## Design (approach A)

### 1. Shared context

`backend/adapters/inference/components/context.py`:

```python
from dataclasses import dataclass
from typing import Any, Callable

@dataclass
class InferenceComponentContext:
    """Cross-cutting collaborators a component needs from its host adapter."""
    log_usage: Callable[..., None]   # bound to adapter._log_usage
    generate: Callable[..., Any]     # bound to adapter.generate (LLM fallbacks)
```

Two fields for the pilot. It will grow as more components migrate (e.g. a clip-model accessor for
the video component), but only with fields a migrated component actually needs (YAGNI).

### 2. Components

New package `backend/adapters/inference/components/`:

- `manga_ocr_component.py` → `MangaOcrComponent`:
  - `__init__(self, ctx: InferenceComponentContext)` storing `self._ctx`; lazy cache
    `self._pipeline = None` lives **on the component**.
  - `process_manga_page(self, image_data: bytes) -> dict` — logic moved verbatim from
    `MangaOcrMixin`, with `self._log_usage(...)` → `self._ctx.log_usage(...)` and the
    `hasattr(self, "_manga_ocr_pipeline")` lazy-load rewritten against `self._pipeline`.

- `rerank_component.py` → `RerankComponent`:
  - `__init__(self, ctx, reranker_model_name="cross-encoder/ms-marco-MiniLM-L-12-v2")`; lazy cache
    `self._cross_encoder = None` on the component.
  - `rerank_documents(self, query, documents) -> list[float]` — logic moved verbatim from
    `RerankMixin`: Cohere path, local CrossEncoder path, then the prompt fallback calling
    `self._ctx.generate(...)`. The Cohere/local `_log_usage` → `self._ctx.log_usage`. The prompt
    fallback's behavior is preserved exactly (see latent bug).

### 3. Adapter changes (`unified_inference_adapter.py`)

- Remove `MangaOcrMixin` and `RerankMixin` from the class bases (8 mixins → 6 + `InferencePort`);
  drop their imports.
- In `__init__`, after the existing setup, build the context and components:
  ```python
  ctx = InferenceComponentContext(log_usage=self._log_usage, generate=self.generate)
  self._manga_ocr = MangaOcrComponent(ctx)
  self._rerank = RerankComponent(ctx)
  ```
  (`self._log_usage` is available from `InferencePort.__init__`; `self.generate` is a bound method
  resolved at call time, so passing it before its definition in the class body is fine.)
- Add two thin delegating methods so capability detection still finds them on the class:
  ```python
  def process_manga_page(self, image_data):
      return self._manga_ocr.process_manga_page(image_data)

  def rerank_documents(self, query, documents):
      return self._rerank.rerank_documents(query, documents)
  ```

#### 4. Old mixin files — left untouched (minimal blast radius)

All eight mixins are **shared**: `MangaOcrMixin` is also inherited by `VisionTransformersAdapter`,
and `RerankMixin` by `LocalRerankAdapter` (verified by grep). They cannot be deleted.

For this low-risk pilot we **leave both mixin files (and every other adapter) completely
untouched**. The new components are used **only by `UnifiedInferenceAdapter`**. This means the
component logic is, transitionally, **duplicated** from the mixin — an accepted, documented cost
(see follow-up). It buys a near-zero blast radius: `VisionTransformersAdapter`, `LocalRerankAdapter`,
their `health_check`s, and all their existing tests are unaffected. The alternative (mixin →
delegating shim, single source) was rejected for the pilot because it would force changes to
`LocalRerankAdapter.health_check` (which reads `self._cross_encoder`) and retargeting of tests that
patch mixin-module internals — broadening the blast radius.

The follow-up (migrate the remaining adapters to the components and delete the mixins, removing the
duplication) is tracked in the TODO.

## Latent bug (preserved, out of scope)

`RerankMixin`'s prompt fallback does `raw = self.generate(...)` then `re.search(r"\[.*\]", raw)`,
but `generate` returns an `InferenceResponse`, not a `str` — so `re.search` raises `TypeError`,
which is caught and the method returns `[0.0] * len(documents)`. The pilot preserves this exactly
and locks it with a characterization test. Fixing it is a separate follow-up.

## Testing (TDD)

- **Characterization (adapter level), written before the refactor:** `rerank_documents([])` → `[]`;
  local CrossEncoder path (CrossEncoder + `safe_http_request`/Cohere mocked) returns the mocked
  scores; prompt-fallback path (local load forced to raise; `generate` returns an
  `InferenceResponse`) returns `[0.0] * n`. These pass on the current mixin-based adapter and must
  still pass after the refactor.
- **Component unit tests (the testability win):** `MangaOcrComponent` and `RerankComponent`
  constructed with a fake `InferenceComponentContext` (a recorder `log_usage`, a stub `generate`);
  heavy model loads (`pipeline`, `CrossEncoder`) and HTTP (`safe_http_request`) mocked. Assert
  `log_usage` is invoked with the right engine string, and the score/return shapes.
- **Capability-detection guard (central):** build `FallbackInferenceAdapter([unified_adapter])` and
  assert `unified_adapter` is in `_capability_cache["rerank_documents"]` and
  `_capability_cache["process_manga_page"]` — proving the delegating methods keep
  `UnifiedInferenceAdapter` routable after it drops the two mixins.
- **Regression guard:** the existing suite must stay green. The other adapters' tests are untouched
  (mixins unchanged); the one Unified-side test that references these methods
  (`tests/adapters/test_brain_api.py`) monkeypatches the methods themselves, so it is unaffected.
  The plan's final task re-runs the inference suites to confirm.
- All tests mock LLM/GPU/HTTP — CI-safe (no live model, no network).

## Risks / mitigations

- **Risk:** delegating method forgotten → fallback silently stops routing a capability.
  *Mitigation:* the capability-detection guard test fails loudly if a delegate is missing.
- **Risk:** behavior drift while moving code. *Mitigation:* characterization tests written first
  on the current adapter; the component logic is moved verbatim.
- **Risk:** context grows into a new god-object. *Mitigation:* add fields only as a migrated
  component needs them; pilot keeps it to two.
- **Risk:** transitional duplication between the components and the still-present mixins drifts over
  time. *Mitigation:* the components are copied verbatim from the mixins now; the TODO follow-up
  (migrate the other adapters to the components, delete the mixins) removes the duplication. Scope
  kept to Unified-only to keep the pilot's blast radius minimal.

## Out of scope / follow-up

- Migrating the other six mixins (each its own task, reusing this template).
- Fixing the rerank prompt-fallback `InferenceResponse`-vs-`str` bug.
