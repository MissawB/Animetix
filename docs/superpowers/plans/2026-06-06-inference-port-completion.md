# InferencePort Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clean up the `InferencePort` interface by removing stubs and `TODO` comments, and ensuring all adapters implement a mandatory core contract.

**Architecture:** Pure Interface pattern for the Port, with mandatory abstract methods for core functionality and standard error-raising for optional ones.

**Tech Stack:** Python 3.11+, ABC, Transformers (local adapters).

---

### Task 1: Refactor InferencePort Interface

**Files:**
- Modify: `backend/core/ports/inference_port.py`
- Test: `tests/core/ports/test_inference_port.py`

- [ ] **Step 1: Write the Port test**

```python
import pytest
from backend.core.ports.inference_port import InferencePort, InferenceNotImplementedError

def test_inference_port_abstract():
    with pytest.raises(TypeError):
        InferencePort()

def test_inference_port_optional_methods():
    class MockAdapter(InferencePort):
        def generate(self, *args, **kwargs): pass
        def stream_generate(self, *args, **kwargs): pass
        def get_text_embedding(self, *args, **kwargs): pass
        def health_check(self, *args, **kwargs): pass
    
    adapter = MockAdapter()
    with pytest.raises(InferenceNotImplementedError):
        adapter.generate_image("test")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/ports/test_inference_port.py`
Expected: FAIL (TypeError: can't instantiate abstract class with abstract methods) - Note: It might pass if the Port is already somewhat abstract, but the "optional methods" test should fail if they still have TODO stubs.

- [ ] **Step 3: Implement clean Interface**

Modify `backend/core/ports/inference_port.py`:
- Mark `generate`, `stream_generate`, `get_text_embedding`, and `health_check` with `@abstractmethod`.
- Remove all `# TODO` comments.
- Clean up optional methods to simply `raise InferenceNotImplementedError("<method_name> not implemented for this adapter")`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/core/ports/test_inference_port.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/core/ports/inference_port.py tests/core/ports/test_inference_port.py
git commit -m "port: formalize InferencePort interface and mandatory contract"
```

---

### Task 2: Standardize LocalTextAdapter

**Files:**
- Modify: `backend/adapters/inference/local_text_adapter.py`
- Test: `tests/adapters/inference/test_local_text_adapter.py`

- [ ] **Step 1: Implement get_text_embedding**

Add to `LocalTextAdapter`:
```python
    def get_text_embedding(self, text: str) -> List[float]:
        """Génère un embedding local via SentenceTransformer."""
        if not hasattr(self, '_embedding_model'):
            from sentence_transformers import SentenceTransformer
            logger.info("🏗️ Loading Local Embedding Model: all-MiniLM-L6-v2")
            self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        self._log_usage(engine="local:all-MiniLM-L6-v2", units=1)
        return self._embedding_model.encode(text).tolist()
```

- [ ] **Step 2: Run existing tests to verify compliance**

Run: `pytest tests/adapters/inference/test_local_text_adapter.py`
Expected: PASS (and verify it can be instantiated)

- [ ] **Step 3: Commit**

```bash
git add backend/adapters/inference/local_text_adapter.py
git commit -m "adapter: implement get_text_embedding for LocalTextAdapter"
```

---

### Task 3: Standardize MoondreamAdapter

**Files:**
- Modify: `backend/adapters/inference/moondream_adapter.py`

- [ ] **Step 1: Implement mandatory methods**

Add `generate`, `stream_generate`, and `get_text_embedding` (as a stub/error) to `MoondreamAdapter`.

- [ ] **Step 2: Commit**

```bash
git add backend/adapters/inference/moondream_adapter.py
git commit -m "adapter: make MoondreamAdapter compliant with mandatory InferencePort contract"
```

---

### Task 4: Final Cleanup and Verification

**Files:**
- Modify: `backend/adapters/inference/*.py`

- [ ] **Step 1: Scan for remaining stubs**

Remove any `# TODO` or `InferenceNotImplementedError` that duplicate the new Port defaults in `BrainAPIAdapter`, `GoogleGenAIAdapter`, etc.

- [ ] **Step 2: Verify full system health**

Run: `pytest tests/api/test_forms.py tests/api/test_schemas.py` (Verify no regressions)

- [ ] **Step 3: Commit**

```bash
git commit -m "cleanup: remove redundant stubs in inference adapters"
```
