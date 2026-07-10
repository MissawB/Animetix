# Inference Environment Variables Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fail early at application startup if `BRAIN_API_URL` is undefined or empty, by raising a custom `ConfigurationError` exception.

**Architecture:** 
- Define a custom `ConfigurationError` exception inheriting from `AnimetixBaseError` in `backend/core/domain/entities/exceptions.py` and export it via `backend/core/domain/exceptions.py`.
- Add validation in `BrainAPIAdapter.__init__` to raise `ConfigurationError` if `api_url` is missing or empty.
- Add validation in `InferenceContainer.__init__` to raise `ConfigurationError` at container initialization/startup, except when running pytest (detected via `PYTEST_CURRENT_TEST` env var).

**Tech Stack:** Python, Django, dependency-injector, pytest

---

### Task 1: Define `ConfigurationError` Exception

**Files:**
- Modify: `backend/core/domain/entities/exceptions.py`
- Modify: `backend/core/domain/exceptions.py`

- [ ] **Step 1: Define `ConfigurationError` in `backend/core/domain/entities/exceptions.py`**
  Add the following definition:
  ```python
  class ConfigurationError(AnimetixBaseError):
      """Raised when environment variables or configurations are missing/invalid."""

      pass
  ```
- [ ] **Step 2: Export `ConfigurationError` in `backend/core/domain/exceptions.py`**
  Add import and export `ConfigurationError`:
  ```python
  from .entities.exceptions import (
      # ... existing imports
      ConfigurationError,
  )

  __all__ = [
      # ... existing exports
      "ConfigurationError",
  ]
  ```
- [ ] **Step 3: Run existing tests to verify no regressions**
  Run: `..\..\.venv\Scripts\pytest tests/adapters/test_brain_api_adapter_v2.py -v`
  Expected: PASS
- [ ] **Step 4: Commit**
  Run:
  ```bash
  git add backend/core/domain/entities/exceptions.py backend/core/domain/exceptions.py
  git commit -m "feat: add ConfigurationError custom exception"
  ```

---

### Task 2: Validate in `BrainAPIAdapter` and Update Adapter Unit Tests

**Files:**
- Modify: `backend/adapters/inference/brain_api_adapter.py`
- Modify: `tests/adapters/test_brain_api_adapter_extra.py`

- [ ] **Step 1: Validate `self.api_url` in `BrainAPIAdapter.__init__`**
  Update `backend/adapters/inference/brain_api_adapter.py` constructor:
  ```python
  from core.domain.exceptions import ConfigurationError

  # In __init__:
  self.api_url = api_url or os.getenv("BRAIN_API_URL")
  if not self.api_url:
      raise ConfigurationError("Brain API URL not configured")
  self.api_key = api_key or os.getenv("BRAIN_API_KEY")
  ```
- [ ] **Step 2: Update existing unit tests in `tests/adapters/test_brain_api_adapter_extra.py`**
  Modify tests that test missing URL to assert `ConfigurationError` is raised on instantiation instead of on `generate` / `stream_generate` / `get_image_embedding`.
  For example, update:
  - `test_generate_raises_when_url_missing`
  - `test_stream_generate_raises_when_url_missing`
  - `test_get_image_embedding_returns_empty_without_url` (which should now raise `ConfigurationError` on initialization if we don't pass `api_url`).
- [ ] **Step 3: Run the adapter unit tests**
  Run: `..\..\.venv\Scripts\pytest tests/adapters/test_brain_api_adapter_extra.py -v`
  Expected: PASS
- [ ] **Step 4: Commit**
  Run:
  ```bash
  git add backend/adapters/inference/brain_api_adapter.py tests/adapters/test_brain_api_adapter_extra.py
  git commit -m "feat: validate BRAIN_API_URL in BrainAPIAdapter and update tests"
  ```

---

### Task 3: Validate in `InferenceContainer` and Test Container Early Failure

**Files:**
- Modify: `backend/api/animetix/containers/inference.py`
- Modify: `tests/core/test_inference_adapters.py`

- [ ] **Step 1: Add early validation check to `InferenceContainer.__init__`**
  Modify `backend/api/animetix/containers/inference.py`:
  ```python
  from core.domain.exceptions import ConfigurationError

  class InferenceContainer(containers.DeclarativeContainer):
      # ... existing providers ...

      def __init__(self, *args, **kwargs):
          super().__init__(*args, **kwargs)
          if not os.environ.get("PYTEST_CURRENT_TEST"):
              brain_api_url = os.getenv("BRAIN_API_URL")
              if not brain_api_url:
                  raise ConfigurationError("BRAIN_API_URL is not configured")
  ```
- [ ] **Step 2: Write unit tests in `tests/core/test_inference_adapters.py`**
  Add tests validating the container initialization failure:
  ```python
  from core.domain.exceptions import ConfigurationError
  from animetix.containers.inference import InferenceContainer

  def test_inference_container_raises_on_missing_url(monkeypatch):
      # Remove PYTEST_CURRENT_TEST and BRAIN_API_URL to test startup check
      monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
      monkeypatch.delenv("BRAIN_API_URL", raising=False)
      
      with pytest.raises(ConfigurationError, match="BRAIN_API_URL is not configured"):
          InferenceContainer()

  def test_inference_container_succeeds_when_url_present(monkeypatch):
      # Simulate URL configuration and verify success
      monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
      monkeypatch.setenv("BRAIN_API_URL", "http://brain-api:7861")
      
      container = InferenceContainer()
      assert container is not None
  ```
- [ ] **Step 3: Run the container tests**
  Run: `..\..\.venv\Scripts\pytest tests/core/test_inference_adapters.py -v`
  Expected: PASS
- [ ] **Step 4: Commit**
  Run:
  ```bash
  git add backend/api/animetix/containers/inference.py tests/core/test_inference_adapters.py
  git commit -m "feat: validate BRAIN_API_URL at InferenceContainer startup and add tests"
  ```
