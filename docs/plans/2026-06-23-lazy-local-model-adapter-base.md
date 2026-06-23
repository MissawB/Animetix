# LazyLocalModelAdapter base (dedup inference adapters, pilot) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Factor the duplicated guarded lazy `_load_model` wrapper + attribute `health_check` into a `LazyLocalModelAdapter` base, and migrate `LocalTextAdapter` + `MoondreamAdapter` onto it — behavior preserved (except a unified error-message text).

**Architecture:** A new `LazyLocalModelAdapter(InferencePort)` owns `_load_model` (guard via `_is_loaded`, `try/except` → `raise InferenceError`, calling the subclass hook `_load_model_impl`) and `health_check` (`{"status": online/offline by _is_ready, "engine": ENGINE_NAME}`). The two "local HF model" adapters subclass it; `CompactReasoningAdapter` (extends `LocalTextAdapter`) benefits transitively and is untouched.

**Tech Stack:** Python 3.12, pytest, `core.domain.exceptions.InferenceError`, `core.ports.inference_port.InferencePort`.

## Global Constraints

- Behavior-preserving: each migrated adapter keeps the same lazy-load guard semantics (`if loaded: return`), the same raise-on-failure (an `InferenceError`), and the same `health_check` dict (status + engine).
- The load *body* is moved VERBATIM into `_load_model_impl` (only the `if self.model: return` guard and the `try/except` wrapper are removed — the base supplies them).
- Accepted behavior change: the `InferenceError` message text is unified to `"Critical failure during {ENGINE_NAME} model loading: {e}"`. Exactly one test asserts the old text (`tests/adapters/test_moondream_adapter.py:188`) and is updated; the exception *type* is unchanged.
- `LocalTextAdapter.get_text_embedding`'s inline embedding load and `CompactReasoningAdapter` are NOT touched.
- All tests mock the model loads — CI-safe (no live HF download / GPU).
- Spec: `docs/specs/2026-06-23-lazy-local-model-adapter-base-design.md`.

---

### Task 1: LazyLocalModelAdapter base + unit tests

**Files:**
- Create: `backend/adapters/inference/lazy_local_model_adapter.py`
- Test: `tests/adapters/inference/test_lazy_local_model_adapter.py`

**Interfaces:**
- Produces: `LazyLocalModelAdapter(InferencePort)` with class attr `ENGINE_NAME: str = "local"`; methods `_load_model() -> None` (guarded wrapper), `_is_loaded() -> bool` (default `getattr(self, "model", None) is not None`), `_load_model_impl() -> None` (hook, raises `NotImplementedError`), `_is_ready() -> bool` (default `self._is_loaded()`), `health_check() -> dict`.

- [ ] **Step 1: Write the failing test**

```python
# tests/adapters/inference/test_lazy_local_model_adapter.py
import pytest

from adapters.inference.lazy_local_model_adapter import LazyLocalModelAdapter
from core.domain.exceptions import InferenceError


class _Fake(LazyLocalModelAdapter):
    ENGINE_NAME = "fake"

    def __init__(self, fail=False):
        super().__init__()
        self.model = None
        self._loads = 0
        self._fail = fail

    def _load_model_impl(self):
        self._loads += 1
        if self._fail:
            raise RuntimeError("boom")
        self.model = object()

    # satisfy the remaining InferencePort abstract methods
    def generate(self, *a, **k):
        ...

    def stream_generate(self, *a, **k):
        ...

    def get_text_embedding(self, *a, **k):
        ...


def test_load_model_calls_impl_when_not_loaded():
    f = _Fake()
    f._load_model()
    assert f._loads == 1 and f.model is not None


def test_load_model_noop_when_loaded():
    f = _Fake()
    f._load_model()
    f._load_model()
    assert f._loads == 1


def test_load_model_wraps_failure_in_inference_error():
    f = _Fake(fail=True)
    with pytest.raises(
        InferenceError, match="Critical failure during fake model loading: boom"
    ):
        f._load_model()
    assert f.model is None  # stays unset so a retry is possible


def test_health_check_offline_then_online():
    f = _Fake()
    assert f.health_check() == {"status": "offline", "engine": "fake"}
    f._load_model()
    assert f.health_check() == {"status": "online", "engine": "fake"}


def test_is_ready_override_is_independent_of_lazy_load_guard():
    class _ReadyFake(_Fake):
        def _is_ready(self):
            return True

    f = _ReadyFake()
    # health uses _is_ready -> online even though the model is not loaded
    assert f.health_check()["status"] == "online"
    # the lazy-load guard uses _is_loaded (model is None) -> still loads
    f._load_model()
    assert f._loads == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/adapters/inference/test_lazy_local_model_adapter.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'adapters.inference.lazy_local_model_adapter'`.

- [ ] **Step 3: Write the implementation**

Create `backend/adapters/inference/lazy_local_model_adapter.py`:

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

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/adapters/inference/test_lazy_local_model_adapter.py -q`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/adapters/inference/lazy_local_model_adapter.py tests/adapters/inference/test_lazy_local_model_adapter.py
git commit -m "feat(inference): LazyLocalModelAdapter base (guarded lazy load + health_check)"
```

---

### Task 2: Migrate MoondreamAdapter onto the base

**Files:**
- Modify: `backend/adapters/inference/moondream_adapter.py` (class declaration; `_load_model` → `_load_model_impl`; remove `health_check`; add `ENGINE_NAME`)
- Modify: `tests/adapters/test_moondream_adapter.py:188` (error-message match)

**Interfaces:**
- Consumes: `LazyLocalModelAdapter` (Task 1).
- Produces: `MoondreamAdapter(LazyLocalModelAdapter)` with `ENGINE_NAME = "SmolVLM"`; the load body lives in `_load_model_impl`; `_load_model`/`health_check` inherited.

- [ ] **Step 1: Update the failing test reference**

In `tests/adapters/test_moondream_adapter.py`, change the match string at the `test_load_model_wraps_loader_failure_in_inference_error` test (currently `match="SmolVLM loading failed: CUDA out of memory"`) to:

```python
    with pytest.raises(
        InferenceError,
        match="Critical failure during SmolVLM model loading: CUDA out of memory",
    ):
        a._load_model()
```

- [ ] **Step 2: Run the Moondream tests to verify the message test now fails**

Run: `python -m pytest tests/adapters/test_moondream_adapter.py -q`
Expected: FAIL — `test_load_model_wraps_loader_failure_in_inference_error` fails (the adapter still raises the OLD message `"SmolVLM loading failed: ..."`). The other Moondream tests still pass.

- [ ] **Step 3: Migrate the adapter**

In `backend/adapters/inference/moondream_adapter.py`:

(a) Add the base import (next to the other inference imports):

```python
from adapters.inference.lazy_local_model_adapter import LazyLocalModelAdapter
```

(b) Change the class declaration and add `ENGINE_NAME` (keep `__init__` as-is):

```python
class MoondreamAdapter(LazyLocalModelAdapter):
    ENGINE_NAME = "SmolVLM"

    def __init__(
        self,
        model_id: str = "HuggingFaceTB/SmolVLM-Instruct",
        usage_port: Optional[UsagePort] = None,
    ):
        super().__init__(usage_port=usage_port)
        self.model_id = model_id
        self.model: Any = None
        self.processor: Any = None
```

(c) Replace the `_load_model` method (the whole `def _load_model(self): ...` block, guard + try/except + body) with `_load_model_impl` holding only the load body:

```python
    def _load_model_impl(self) -> None:
        import torch as _torch  # noqa: E402
        from transformers import (
            AutoModelForVision2Seq,  # noqa: E402
            AutoProcessor,
        )

        self.model = AutoModelForVision2Seq.from_pretrained(
            self.model_id,
            revision=trusted_revision(self.model_id) or "main",
            trust_remote_code=resolve_trust_remote_code(self.model_id),
            device_map="auto",
            torch_dtype=(
                _torch.bfloat16 if _torch.cuda.is_available() else _torch.float32
            ),
        )
        self.processor = AutoProcessor.from_pretrained(
            self.model_id, revision=trusted_revision(self.model_id) or "main"
        )
```

(d) Delete the `health_check` method (the base provides it; the default `_is_ready == _is_loaded == self.model` matches the old `{"status": online if self.model, "engine": "SmolVLM"}`).

- [ ] **Step 4: Run the Moondream tests to verify they pass**

Run: `python -m pytest tests/adapters/test_moondream_adapter.py -q`
Expected: PASS (all). The caching test (`_load_model` thrice → loads once) passes via the base guard; the health tests pass via the inherited `health_check`; the failure test now matches the unified message.

- [ ] **Step 5: Commit**

```bash
git add backend/adapters/inference/moondream_adapter.py tests/adapters/test_moondream_adapter.py
git commit -m "refactor(inference): MoondreamAdapter extends LazyLocalModelAdapter"
```

---

### Task 3: Migrate LocalTextAdapter onto the base

**Files:**
- Modify: `backend/adapters/inference/local_text_adapter.py` (class declaration; `_load_model` → `_load_model_impl`; remove `health_check`; add `ENGINE_NAME` + `_is_ready` override)

**Interfaces:**
- Consumes: `LazyLocalModelAdapter` (Task 1).
- Produces: `LocalTextAdapter(LazyLocalModelAdapter)` with `ENGINE_NAME = "local_text"`, `_is_ready` overridden to `self.model is not None or self._embedding_model is not None`.

- [ ] **Step 1: Confirm the existing LocalText tests are the guard**

Run: `python -m pytest tests/adapters/inference/test_local_text_adapter.py -q`
Expected: PASS (baseline before the change). `test_health_check` (offline → online after `self.model` is set) and `test_get_text_embedding_lazy_loading` must remain green after the migration.

- [ ] **Step 2: Migrate the adapter**

In `backend/adapters/inference/local_text_adapter.py`:

(a) Add the base import (next to the other inference imports):

```python
from adapters.inference.lazy_local_model_adapter import LazyLocalModelAdapter
```

(b) Change the class declaration and add `ENGINE_NAME` (keep `__init__` body as-is):

```python
class LocalTextAdapter(LazyLocalModelAdapter):
    ENGINE_NAME = "local_text"
```

(c) Replace the `_load_model` method (guard + try/except + body) with `_load_model_impl` holding only the load body:

```python
    def _load_model_impl(self) -> None:
        from transformers import (
            AutoModelForCausalLM,  # noqa: E402
            AutoTokenizer,
            BitsAndBytesConfig,
        )

        logger.info(f"🏗️ Loading Local Text Model: {self.model_id}")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_id, revision=trusted_revision(self.model_id) or "main"
        )
        quantization_config = (
            BitsAndBytesConfig(load_in_4bit=True) if self.use_4bit else None
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            revision=trusted_revision(self.model_id) or "main",
            device_map="auto",
            quantization_config=quantization_config,
            trust_remote_code=resolve_trust_remote_code(self.model_id),
        )

        if self.speculative_enabled and self.draft_model_id:
            logger.info(f"🏗️ Loading Draft Assistant Model: {self.draft_model_id}")
            self.draft_model = AutoModelForCausalLM.from_pretrained(
                self.draft_model_id,
                revision=trusted_revision(self.draft_model_id) or "main",
                device_map="auto",
                quantization_config=quantization_config,
                trust_remote_code=resolve_trust_remote_code(self.draft_model_id),
            )
```

(d) Replace the `health_check` method with an `_is_ready` override preserving the broader signal:

```python
    def _is_ready(self) -> bool:
        return self.model is not None or self._embedding_model is not None
```

- [ ] **Step 3: Run the LocalText tests to verify they pass**

Run: `python -m pytest tests/adapters/inference/test_local_text_adapter.py -q`
Expected: PASS (all). `test_health_check` is satisfied by the inherited `health_check` + the `_is_ready` override; `_load_model` (now inherited) still loads on first use and guards via `_is_loaded`.

- [ ] **Step 4: Commit**

```bash
git add backend/adapters/inference/local_text_adapter.py
git commit -m "refactor(inference): LocalTextAdapter extends LazyLocalModelAdapter"
```

---

### Task 4: Verification sweep

**Files:**
- Verify only (no new product code).

- [ ] **Step 1: Run the adapter suites + the CompactReasoning guard**

Run: `python -m pytest tests/adapters -q -p no:cacheprovider`
Then (CompactReasoning is transitively affected): `python -m pytest -q -p no:cacheprovider -k "compact_reasoning or CompactReasoning"`
Expected: PASS (no NEW failures vs. before the change; any pre-existing `@pytest.mark.integration` failures needing a live LLM/GPU may remain). Confirm no adapter still defines a duplicate `_load_model` guard/try-except or attribute `health_check` that this pilot was meant to remove for these two adapters:
Run: `grep -n "def _load_model\b\|def health_check" backend/adapters/inference/local_text_adapter.py backend/adapters/inference/moondream_adapter.py`
Expected: neither file defines `_load_model` or `health_check` anymore (they define `_load_model_impl` / `_is_ready` instead).

- [ ] **Step 2: Lint**

Run: `python -m ruff check backend/adapters/inference/lazy_local_model_adapter.py backend/adapters/inference/local_text_adapter.py backend/adapters/inference/moondream_adapter.py`
Run: `python -m ruff format backend/adapters/inference/lazy_local_model_adapter.py backend/adapters/inference/local_text_adapter.py backend/adapters/inference/moondream_adapter.py tests/adapters/inference/test_lazy_local_model_adapter.py tests/adapters/test_moondream_adapter.py`
Expected: All checks passed; format clean.

- [ ] **Step 3: Commit (only if ruff format changed files)**

```bash
git add -A
git commit -m "style: ruff format for LazyLocalModelAdapter extraction"
```

---

## Notes for the executor

- Do NOT change `CompactReasoningAdapter`, `LocalTextAdapter.get_text_embedding`, or any adapter other than the two named — the pilot is scoped to those two + the new base.
- The other attribute-`health_check` adapters and other lazy-loads are TODO follow-ups (a future `HealthCheckMixin` can reuse `_is_ready`/`ENGINE_NAME`).
