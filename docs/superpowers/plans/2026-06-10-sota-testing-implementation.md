# SOTA Services Testing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement comprehensive unit and integration test coverage for `SelfEvolvingCompiler`, `SynapticPlasticityService`, and `LiquidNeuralNetworkService`.

**Architecture:** Utilize `pytest` for testing, with `unittest.mock` for infrastructure ports. Follow TDD principles for each service.

**Tech Stack:** Python 3.11+, Pytest, Unittest.mock

---

### Task 1: Test `SelfEvolvingCompiler`

**Files:**
- Create: `tests/core/test_self_evolving_compiler.py`
- Modify: `backend/core/domain/services/self_evolving_compiler.py` (if needed for testability)

- [ ] **Step 1: Write unit test for compiler core logic**
*(Assuming basic compilation check)*
```python
import pytest
from backend.core.domain.services.self_evolving_compiler import SelfEvolvingCompiler

def test_compiler_initialization():
    compiler = SelfEvolvingCompiler()
    assert compiler is not None
```

- [ ] **Step 2: Run test to verify it fails/passes**
Run: `pytest tests/core/test_self_evolving_compiler.py`

- [ ] **Step 3: Commit**
```bash
git add tests/core/test_self_evolving_compiler.py
git commit -m "test: add unit tests for SelfEvolvingCompiler"
```

### Task 2: Test `SynapticPlasticityService`

**Files:**
- Create: `tests/core/test_synaptic_plasticity_service.py`

- [ ] **Step 1: Write integration test with mock infrastructure**
```python
import pytest
from unittest.mock import MagicMock
from backend.core.domain.services.synaptic_plasticity import SynapticPlasticityService

def test_plasticity_service_integration():
    mock_inference = MagicMock()
    service = SynapticPlasticityService(inference_engine=mock_inference)
    # Trigger interaction and verify mock
    service.apply_plasticity(data={})
    assert mock_inference.called
```

- [ ] **Step 2: Run test**
Run: `pytest tests/core/test_synaptic_plasticity_service.py`

- [ ] **Step 3: Commit**
```bash
git add tests/core/test_synaptic_plasticity_service.py
git commit -m "test: add integration tests for SynapticPlasticityService"
```

### Task 3: Test `LiquidNeuralNetworkService`

**Files:**
- Modify: `tests/core/test_neuromorphic_lnn_service.py`

- [ ] **Step 1: Add integration tests to existing file**
```python
from unittest.mock import MagicMock
from backend.core.domain.services.neuromorphic_lnn_service import LiquidNeuralNetworkService

def test_lnn_service_interaction():
    mock_inference = MagicMock()
    service = LiquidNeuralNetworkService(inference_engine=mock_inference)
    service.process(input_data=[0.1, 0.2])
    assert mock_inference.called
```

- [ ] **Step 2: Run test**
Run: `pytest tests/core/test_neuromorphic_lnn_service.py`

- [ ] **Step 3: Commit**
```bash
git add tests/core/test_neuromorphic_lnn_service.py
git commit -m "test: enhance tests for LiquidNeuralNetworkService"
```
