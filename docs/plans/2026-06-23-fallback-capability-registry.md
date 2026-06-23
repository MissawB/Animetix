# FallbackInferenceAdapter — extract CapabilityRegistry (pilot) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move capability detection out of `FallbackInferenceAdapter` into a focused, unit-testable `CapabilityRegistry`, with the orchestrator delegating to it — behavior unchanged.

**Architecture:** A new `CapabilityRegistry` owns the `InferencePort` introspection and the method→adapters cache (`is_method_overridden`, `for_method`, `rebuild`). `FallbackInferenceAdapter` builds one in `__init__`, reads capability via `for_method`, rebuilds it in `set_primary_adapter`, and drops the three capability members. Three external test references are updated to the registry's public API.

**Tech Stack:** Python 3.12, pytest, `inspect`, `core.ports.inference_port.InferencePort`.

## Global Constraints

- Behavior-preserving: `FallbackInferenceAdapter`'s observable behavior is unchanged (routing, `set_primary_adapter` rebuild, the empty→fall-back-to-all logic in the orchestrator).
- The detection logic is moved **verbatim** (only `_is_method_overridden` → public `is_method_overridden`; inline imports hoisted to module level).
- Only `fallback_adapter.py` + the new registry file change in product code; only 3 test references are updated, plus new registry tests + one delegation guard.
- The pre-existing `startswith("Erreur")` failure check and selection/health/reporting are NOT touched.
- Spec: `docs/specs/2026-06-23-fallback-capability-registry-design.md`.

---

### Task 1: CapabilityRegistry + unit tests

**Files:**
- Create: `backend/adapters/inference/capability_registry.py`
- Test: `tests/adapters/test_capability_registry.py`

**Interfaces:**
- Produces: `CapabilityRegistry(adapters: list[InferencePort])`; `for_method(method_name: str) -> list[InferencePort]`; `rebuild(adapters: list[InferencePort]) -> None`; `@staticmethod is_method_overridden(adapter, method_name: str) -> bool`.

- [ ] **Step 1: Write the failing test**

```python
# tests/adapters/test_capability_registry.py
from unittest.mock import MagicMock

from adapters.inference.capability_registry import CapabilityRegistry
from core.ports.inference_port import InferencePort


class _Base(InferencePort):
    def generate(self, *a, **k):
        raise NotImplementedError

    def stream_generate(self, *a, **k):
        raise NotImplementedError

    def get_text_embedding(self, *a, **k):
        raise NotImplementedError

    def health_check(self):
        return {"status": "offline"}


class _Generic(_Base):
    pass  # does NOT override estimate_depth -> inherits the port default


class _Capable(_Base):
    def estimate_depth(self, image_data):
        return b"depth"


def test_is_method_overridden_true_for_override():
    assert CapabilityRegistry.is_method_overridden(_Capable(), "estimate_depth") is True


def test_is_method_overridden_false_for_port_default():
    assert CapabilityRegistry.is_method_overridden(_Generic(), "estimate_depth") is False


def test_is_method_overridden_ignores_mocks():
    assert CapabilityRegistry.is_method_overridden(MagicMock(), "estimate_depth") is False


def test_for_method_returns_only_capable_in_order():
    g, c = _Generic(), _Capable()
    reg = CapabilityRegistry([g, c])
    assert reg.for_method("estimate_depth") == [c]


def test_for_method_empty_when_none_capable():
    reg = CapabilityRegistry([_Generic()])
    assert reg.for_method("estimate_depth") == []


def test_rebuild_reflects_reordering():
    a, b = _Capable(), _Capable()
    reg = CapabilityRegistry([a, b])
    assert reg.for_method("estimate_depth") == [a, b]
    reg.rebuild([b, a])
    assert reg.for_method("estimate_depth") == [b, a]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/adapters/test_capability_registry.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'adapters.inference.capability_registry'`.

- [ ] **Step 3: Write the implementation**

Create `backend/adapters/inference/capability_registry.py`:

```python
import inspect
import logging
from typing import Dict, List

from core.ports.inference_port import InferencePort

logger = logging.getLogger("animetix.inference.capability_registry")


class CapabilityRegistry:
    """Detects which adapters override which InferencePort methods, and caches it.

    The detection is class-based (an adapter "has" a capability iff its class
    overrides the corresponding InferencePort method), moved verbatim out of
    FallbackInferenceAdapter.
    """

    def __init__(self, adapters: List[InferencePort]):
        self._cache: Dict[str, List[InferencePort]] = {}
        self.rebuild(adapters)

    def for_method(self, method_name: str) -> List[InferencePort]:
        """Adapters that override `method_name`, in adapter order; [] if none."""
        return self._cache.get(method_name, [])

    def rebuild(self, adapters: List[InferencePort]) -> None:
        """Rebuild the cache from the given adapter list (order preserved)."""
        port_methods = [
            name
            for name, _val in inspect.getmembers(
                InferencePort, predicate=inspect.isfunction
            )
            if not name.startswith("_")
        ]
        self._cache = {}
        for method_name in port_methods:
            capable = [
                adapter
                for adapter in adapters
                if self.is_method_overridden(adapter, method_name)
            ]
            self._cache[method_name] = capable
            logger.debug(
                f"⚙️ [CapabilityRegistry] '{method_name}': "
                f"{[a.__class__.__name__ for a in capable]}"
            )

    @staticmethod
    def is_method_overridden(adapter: InferencePort, method_name: str) -> bool:
        # Ignore mock objects to avoid registering instance-level mock methods.
        if getattr(adapter.__class__, "__module__", "") == "unittest.mock" or hasattr(
            adapter, "mock_calls"
        ):
            return False

        cls = adapter.__class__
        method = getattr(cls, method_name, None)
        if method is None or not callable(method):
            return False

        port_method = getattr(InferencePort, method_name, None)
        if port_method is None:
            return True

        adapter_func = getattr(method, "__func__", method)
        port_func = getattr(port_method, "__func__", port_method)
        return adapter_func is not port_func
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/adapters/test_capability_registry.py -q`
Expected: PASS (6 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/adapters/inference/capability_registry.py tests/adapters/test_capability_registry.py
git commit -m "feat(inference): CapabilityRegistry (extracted adapter-capability detection)"
```

---

### Task 2: Delegate from FallbackInferenceAdapter + update references

**Files:**
- Modify: `backend/adapters/inference/fallback_adapter.py` (imports; `__init__` lines 23/31; the three `_capability_cache.get(...)` reads at lines 142, 219, 381; `set_primary_adapter` line 603; delete `_is_method_overridden` lines 58-77 and `_build_capability_cache` lines 79-101)
- Modify: `tests/adapters/test_fallback_structured.py` (lines 87-88, 91)
- Modify: `tests/adapters/test_unified_inference_composition.py` (lines 53-54)
- Test: `tests/adapters/test_fallback_capability_delegation.py` (new)

**Interfaces:**
- Consumes: `CapabilityRegistry` (Task 1).
- Produces: `FallbackInferenceAdapter` exposes `self._capabilities: CapabilityRegistry`; no longer has `_capability_cache`, `_is_method_overridden`, or `_build_capability_cache`.

- [ ] **Step 1: Write the failing delegation guard test**

```python
# tests/adapters/test_fallback_capability_delegation.py
from adapters.inference.capability_registry import CapabilityRegistry
from adapters.inference.fallback_adapter import FallbackInferenceAdapter
from core.ports.inference_port import InferencePort


class _Base(InferencePort):
    def generate(self, *a, **k):
        return None

    def stream_generate(self, *a, **k):
        yield None

    def get_text_embedding(self, *a, **k):
        return []

    def health_check(self):
        return {"status": "offline"}


class _A(_Base):
    pass


class _B(_Base):
    pass


def test_adapter_exposes_capability_registry():
    fb = FallbackInferenceAdapter([_A(), _B()])
    assert isinstance(fb._capabilities, CapabilityRegistry)
    assert not hasattr(fb, "_capability_cache")
    assert not hasattr(fb, "_build_capability_cache")
    assert not hasattr(fb, "_is_method_overridden")


def test_generate_capability_routed_via_registry():
    a, b = _A(), _B()
    fb = FallbackInferenceAdapter([a, b])
    capable = fb._capabilities.for_method("generate")
    assert a in capable and b in capable


def test_set_primary_adapter_rebuilds_capabilities():
    a, b = _A(), _B()
    fb = FallbackInferenceAdapter([a, b])
    assert fb._capabilities.for_method("generate") == [a, b]
    assert fb.set_primary_adapter(1) is True
    assert fb._capabilities.for_method("generate") == [b, a]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/adapters/test_fallback_capability_delegation.py -q`
Expected: FAIL — `AttributeError: 'FallbackInferenceAdapter' object has no attribute '_capabilities'`.

- [ ] **Step 3: Apply the adapter edits**

(a) Add the import near the other inference imports at the top of `fallback_adapter.py`:

```python
from adapters.inference.capability_registry import CapabilityRegistry
```

(b) In `__init__`, delete this line:

```python
        self._capability_cache: Dict[str, List[InferencePort]] = {}
```

and replace the `self._build_capability_cache()` call (the last line of `__init__`) with:

```python
        self._capabilities = CapabilityRegistry(self.adapters)
```

so the tail of `__init__` reads:

```python
        self._check_initial_health()
        self._capabilities = CapabilityRegistry(self.adapters)
```

(c) Delete the two methods `_is_method_overridden` (the whole `def _is_method_overridden(...)` block) and `_build_capability_cache` (the whole `def _build_capability_cache(...)` block).

(d) Replace the three capability reads:
- in `generate`: `capable_adapters = self._capability_cache.get("generate", [])` → `capable_adapters = self._capabilities.for_method("generate")`
- in `stream_generate`: `capable_adapters = self._capability_cache.get("stream_generate", [])` → `capable_adapters = self._capabilities.for_method("stream_generate")`
- in `_fallback_call`: `capable_adapters = self._capability_cache.get(method_name, [])` → `capable_adapters = self._capabilities.for_method(method_name)`

(e) In `set_primary_adapter`, replace `self._build_capability_cache()` with:

```python
            self._capabilities.rebuild(self.adapters)
```

- [ ] **Step 4: Update the three external test references**

In `tests/adapters/test_fallback_structured.py`, add the import at the top:

```python
from adapters.inference.capability_registry import CapabilityRegistry
```

and replace lines 87-88 and 91:

```python
    assert CapabilityRegistry.is_method_overridden(adapter2, "estimate_depth") is True
    assert CapabilityRegistry.is_method_overridden(adapter1, "estimate_depth") is False

    # Capability cache verification
    capable = fallback._capabilities.for_method("estimate_depth")
```

In `tests/adapters/test_unified_inference_composition.py`, replace lines 53-54:

```python
    assert a in fb._capabilities.for_method("rerank_documents")
    assert a in fb._capabilities.for_method("process_manga_page")
```

- [ ] **Step 5: Run the affected tests to verify they pass**

Run: `python -m pytest tests/adapters/test_fallback_capability_delegation.py tests/adapters/test_fallback_structured.py tests/adapters/test_unified_inference_composition.py tests/adapters/test_fallback_adapter.py -q`
Expected: PASS (all). If any test still references `_capability_cache`/`_is_method_overridden`/`_build_capability_cache`, fix that reference (do not re-add the removed members).

- [ ] **Step 6: Commit**

```bash
git add backend/adapters/inference/fallback_adapter.py tests/adapters/test_fallback_capability_delegation.py tests/adapters/test_fallback_structured.py tests/adapters/test_unified_inference_composition.py
git commit -m "refactor(inference): FallbackInferenceAdapter delegates capability detection to CapabilityRegistry"
```

---

### Task 3: Verification sweep

**Files:**
- Verify only (no new product code).

- [ ] **Step 1: Run the adapter + fallback suites**

Run: `python -m pytest tests/adapters tests/core/test_fallback_adapter.py -q -p no:cacheprovider`
Expected: PASS (no NEW failures vs. before this change; any pre-existing `@pytest.mark.integration` failures needing a live LLM/GPU may remain). Confirm no test references the removed members:
Run: `grep -rn "_capability_cache\|_is_method_overridden\|_build_capability_cache" backend tests --include="*.py"`
Expected: matches only in `backend/adapters/inference/capability_registry.py` (the new home) — none on `FallbackInferenceAdapter` or in tests (the unrelated `_reset_capability_caches` in `tests/pipeline/test_vector_client_behavior.py` is a different name and may remain).

- [ ] **Step 2: Lint**

Run: `python -m ruff check backend/adapters/inference/capability_registry.py backend/adapters/inference/fallback_adapter.py`
Run: `python -m ruff format backend/adapters/inference/capability_registry.py backend/adapters/inference/fallback_adapter.py tests/adapters/test_capability_registry.py tests/adapters/test_fallback_capability_delegation.py`
Expected: All checks passed; format clean.

- [ ] **Step 3: Commit (only if ruff format changed files)**

```bash
git add -A
git commit -m "style: ruff format for CapabilityRegistry extraction"
```

---

## Notes for the executor

- Do NOT touch selection/health (`_check_initial_health`, `_get_ordered_adapters`, `_online_adapters`), `_report_failure`, or the orchestration bodies beyond the capability-read substitutions listed.
- `Dict`/`List` typing imports in `fallback_adapter.py` are still used elsewhere in the file — keep them.
