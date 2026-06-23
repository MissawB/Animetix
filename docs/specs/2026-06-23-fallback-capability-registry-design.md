# Design — FallbackInferenceAdapter: extract CapabilityRegistry (pilot)

**Date:** 2026-06-23
**Status:** Approved (approach A; pilot scope)
**TODO source:** "Backend — `FallbackInferenceAdapter` god object + couplage central — extract selection/health-check from orchestration"

## Problem

`FallbackInferenceAdapter` (`backend/adapters/inference/fallback_adapter.py`, ~703 lines) bundles
four responsibilities: capability detection, adapter selection/health, failure reporting, and the
fallback orchestration itself. ~60 services depend on it (the inference engine), so it is the
hardest coupling point to evolve.

This is a **pilot**: extract exactly one responsibility — **capability detection** — into a
focused, independently testable `CapabilityRegistry`, leaving selection/health, reporting, and
orchestration for follow-ups. It is a **behavior-preserving** refactor.

## Current state (verified)

Capability detection lives on the adapter as:
- `self._capability_cache: Dict[str, List[InferencePort]]` (built in `__init__`).
- `_is_method_overridden(adapter, method_name) -> bool` — true iff the adapter's **class** overrides
  the named `InferencePort` method (and the adapter is not a mock).
- `_build_capability_cache()` — iterates `InferencePort`'s public methods via
  `inspect.getmembers(..., predicate=inspect.isfunction)` and maps each to the capable adapters.

Consumers inside the adapter: `generate`, `stream_generate`, `_fallback_call` read
`self._capability_cache.get(name, [])` then fall back to `self.adapters` when empty;
`set_primary_adapter` reorders `self.adapters` then calls `_build_capability_cache()`.

External references (the entire blast radius — verified by grep):
- `tests/adapters/test_fallback_structured.py` — calls `fallback._is_method_overridden(...)` and
  `fallback._capability_cache.get("estimate_depth", [])`.
- `tests/adapters/test_unified_inference_composition.py` — asserts membership in
  `fb._capability_cache.get("rerank_documents"/"process_manga_page", [])` (the routing guard).
- (`tests/pipeline/test_vector_client_behavior.py`'s `_reset_capability_caches` is an unrelated
  name collision — not the fallback's cache.)

## Goals / non-goals

**Goals**
1. Move capability detection (introspection + cache) into a `CapabilityRegistry` class.
2. `FallbackInferenceAdapter` delegates to the registry; its observable behavior is unchanged,
   including capability routing and `set_primary_adapter` rebuild semantics.
3. The registry is unit-testable in isolation.

**Non-goals**
- Extracting selection/health, reporting, or orchestration (follow-ups; stay in the TODO).
- Any behavior change. The pre-existing `startswith("Erreur")` failure check is untouched (and is
  unrelated to this work).

## Design (approach A)

### 1. CapabilityRegistry (new)

`backend/adapters/inference/capability_registry.py`:

```python
class CapabilityRegistry:
    """Detects which adapters override which InferencePort methods."""

    def __init__(self, adapters: list[InferencePort]):
        self._cache: dict[str, list[InferencePort]] = {}
        self.rebuild(adapters)

    def for_method(self, method_name: str) -> list[InferencePort]:
        """Adapters that override `method_name` (in adapter order); [] if none."""
        return self._cache.get(method_name, [])

    def rebuild(self, adapters: list[InferencePort]) -> None:
        """Rebuild the cache from the given adapter list (order preserved)."""
        # inspect.getmembers(InferencePort, predicate=inspect.isfunction), public names;
        # for each: [a for a in adapters if self.is_method_overridden(a, name)]

    @staticmethod
    def is_method_overridden(adapter, method_name: str) -> bool:
        # moved verbatim from FallbackInferenceAdapter._is_method_overridden:
        # ignore mocks; compare adapter.__class__'s method identity vs InferencePort's.
```

The introspection and detection logic are moved **verbatim** from the adapter (only renamed
`_is_method_overridden` → public `is_method_overridden`). `for_method` returns `[]` when a method
has no capable adapter, so the orchestrator keeps its existing `if not capable: capable =
self.adapters` fallback — behavior identical.

### 2. FallbackInferenceAdapter (modified)

- `__init__`: replace `self._capability_cache = {}` + `self._build_capability_cache()` with
  `self._capabilities = CapabilityRegistry(self.adapters)`.
- Replace the reads `self._capability_cache.get(name, [])` with `self._capabilities.for_method(name)`
  in `generate`, `stream_generate`, and `_fallback_call`.
- `set_primary_adapter`: replace `self._build_capability_cache()` with
  `self._capabilities.rebuild(self.adapters)`.
- Delete `_is_method_overridden`, `_build_capability_cache`, and the `_capability_cache` attribute.
- Selection/health (`_check_initial_health`, `_online_adapters`, `_get_ordered_adapters`),
  reporting (`_report_failure`), and all orchestration methods are **unchanged** apart from the
  wiring above.

### 3. Tests

- **Registry unit tests (the win):** construct real `InferencePort` subclasses (not mocks — the
  detector ignores mocks by design) and assert `is_method_overridden` (override vs port default,
  mock-ignored), `for_method` returns the right adapters in order, and `rebuild` reflects a
  reordering.
- **Update the 3 external references** to the registry's public API:
  `test_fallback_structured.py` → `CapabilityRegistry.is_method_overridden(adapter, name)` and
  `fallback._capabilities.for_method(name)`; `test_unified_inference_composition.py` →
  `fb._capabilities.for_method(name)`.
- **Routing characterization guard:** a test on `FallbackInferenceAdapter` asserting it still routes
  `generate` to a capable adapter via `_capabilities.for_method("generate")`, and that
  `set_primary_adapter` rebuilds so `for_method` reflects the new order.
- The full `tests/adapters` suite stays green (regression gate).

## Risks / mitigations

- **Risk:** a missed `_capability_cache` reference inside the adapter → AttributeError.
  *Mitigation:* delete the attribute and let the routing-guard + full-suite run surface any miss.
- **Risk:** `rebuild` semantics differ from in-place rebuild (order). *Mitigation:* `rebuild` takes
  the current `self.adapters` list and re-iterates it, identical to the old `_build_capability_cache`.
- **Risk:** behavior drift in detection. *Mitigation:* logic moved verbatim; registry unit tests +
  the routing guard lock it.

## Out of scope / follow-up

- Extract selection/health (`AdapterHealthSelector`), then reporting, then slim the orchestrator —
  each its own task in the TODO.
