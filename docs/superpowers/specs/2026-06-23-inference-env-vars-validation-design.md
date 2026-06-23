# Design Specification: Backend Inference Environment Variable Validation

This document outlines the design for early validation of inference environment variables (specifically `BRAIN_API_URL`) at startup.

## Problem Description
Currently, `BrainAPIAdapter` initializes silently with an empty string if the `BRAIN_API_URL` environment variable is not defined. It only fails at runtime when a generation call is executed. This makes configuration errors hard to detect until actual inference tasks are invoked.

## Goals
- Add early validation for `BRAIN_API_URL` at application startup.
- Prevent application initialization if the variable is missing/empty, except when running tests (to avoid breaking pytest environment imports).
- Introduce a custom `ConfigurationError` exception.
- Update tests to assert correct startup and adapter behavior when configuration is missing.

## Proposed Changes

### Exception Definition
A new custom error, `ConfigurationError`, will be defined within the core domain exception hierarchy.
- **File**: `backend/core/domain/entities/exceptions.py`
  ```python
  class ConfigurationError(AnimetixBaseError):
      """Raised when environment variables or configurations are missing/invalid."""
      pass
  ```
- **File**: `backend/core/domain/exceptions.py`
  Export it to public domain exceptions.

### Adapter Initialization Validation
`BrainAPIAdapter` will now validate its configuration during initialization.
- **File**: `backend/adapters/inference/brain_api_adapter.py`
  ```python
  from core.domain.exceptions import ConfigurationError

  # In __init__
  self.api_url = api_url or os.getenv("BRAIN_API_URL")
  if not self.api_url:
      raise ConfigurationError("Brain API URL not configured")
  ```

### Early Startup Validation in Container
Validation is run early when the `InferenceContainer` is instantiated.
- **File**: `backend/api/animetix/containers/inference.py`
  ```python
  from core.domain.exceptions import ConfigurationError

  class InferenceContainer(containers.DeclarativeContainer):
      # ...
      def __init__(self, *args, **kwargs):
          super().__init__(*args, **kwargs)
          if not os.environ.get("PYTEST_CURRENT_TEST"):
              brain_api_url = os.getenv("BRAIN_API_URL")
              if not brain_api_url:
                  raise ConfigurationError("BRAIN_API_URL is not configured")
  ```

## Verification Plan

### Automated Tests
- Adapt existing adapter unit tests in `tests/adapters/test_brain_api_adapter_extra.py` to expect `ConfigurationError` on initialization.
- Add test cases in `tests/core/test_inference_adapters.py` to assert that:
  - Container initialization fails with `ConfigurationError` when `BRAIN_API_URL` is missing and `PYTEST_CURRENT_TEST` is unset/mocked.
  - Container initialization succeeds when `BRAIN_API_URL` is set.
