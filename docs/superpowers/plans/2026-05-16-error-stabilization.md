# Error Handling Stabilization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Systematically replace silent failures (`except: pass`) with structured logging and explicit exception handling across AI services and adapters.

**Architecture:** We will maintain the Hexagonal boundaries while improving observability. Each layer (Domain and Adapter) will now log its own specific failures, allowing the `Orchestrator` to make informed decisions instead of proceeding with incomplete data.

**Tech Stack:** Python 3.10+, Standard `logging` module, `orjson`.

---

### Task 1: Stabilize AgenticRAGService

**Files:**
- Modify: `backend/core/domain/services/agentic_rag_service.py`
- Test: `tests/core/test_agentic_rag_service.py`

- [ ] **Step 1: Write the failing test for JSON parsing error**
```python
import pytest
from unittest.mock import MagicMock
from core.domain.services.agentic_rag_service import AgenticRAGService

def test_extract_json_logs_error_on_invalid_json():
    # Setup
    service = AgenticRAGService(inference_engine=MagicMock(), web_search=MagicMock())
    invalid_json_text = "Here is some text with { invalid json }"
    
    # We want to verify it logs instead of just passing
    with pytest.LogCaptureFixture() as log:
        res = service._extract_json(invalid_json_text)
        assert res == {}
        # This will fail currently as there is no logging
        assert "Failed to parse JSON" in log.text
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/core/test_agentic_rag_service.py -v`

- [ ] **Step 3: Implement structured logging and specific catch blocks**
```python
# In backend/core/domain/services/agentic_rag_service.py

def _extract_json(self, text: str) -> Dict:
    try:
        if '{' in text and '}' in text:
            json_str = text[text.find('{'):text.rfind('}')+1]
            return orjson.loads(json_str)
    except orjson.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from AI output: {e}. Output was: {text[:200]}...")
    except Exception as e:
        logger.error(f"Unexpected error during JSON extraction: {e}")
    return {}
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/core/test_agentic_rag_service.py -v`

- [ ] **Step 5: Commit**
```bash
git add backend/core/domain/services/agentic_rag_service.py
git commit -m "chore: stabilize JSON extraction in AgenticRAGService"
```

---

### Task 2: Stabilize OrchestratorAgentService

**Files:**
- Modify: `backend/core/domain/services/orchestrator_agent_service.py`
- Test: `tests/core/test_orchestrator_agent_service.py`

- [ ] **Step 1: Update error handling in agent invocation loop**
Replace `except: pass` in `_parallel_invoke` or similar methods with logging that identifies which agent failed and why.

- [ ] **Step 2: Write minimal implementation**
```python
# In backend/core/domain/services/orchestrator_agent_service.py
# (Locate the loop where agents are called)
try:
    # agent call
    pass
except Exception as e:
    logger.error(f"Agent {agent_name} failed: {e}", exc_info=True)
    # optionally inject an error observation into history
```

- [ ] **Step 3: Verify with existing tests**
Run: `pytest tests/core/test_orchestrator_agent_service.py`

- [ ] **Step 4: Commit**
```bash
git add backend/core/domain/services/orchestrator_agent_service.py
git commit -m "chore: add telemetry to OrchestratorAgentService failures"
```

---

### Task 3: Robustify Inference Adapters (BrainAPI & vLLM)

**Files:**
- Modify: `backend/adapters/inference/brain_api_adapter.py`
- Modify: `backend/adapters/inference/vllm_adapter.py`

- [ ] **Step 1: Update BrainAPIAdapter to log request failures**
```python
# In backend/adapters/inference/brain_api_adapter.py
try:
    res = requests.post(...)
    res.raise_for_status()
    return res.json().get("text", "")
except requests.exceptions.RequestException as e:
    logger.error(f"BrainAPI Request failed: {e}")
except Exception as e:
    logger.error(f"Unexpected BrainAPI error: {e}")
```

- [ ] **Step 2: Update VllmAdapter to log connection errors**
```python
# In backend/adapters/inference/vllm_adapter.py
try:
    res = requests.post(...)
    # ...
except requests.exceptions.ConnectionError:
    logger.error(f"vLLM server at {self.api_base} is unreachable.")
except Exception as e:
    logger.error(f"vLLM Adapter error: {e}")
```

- [ ] **Step 3: Commit**
```bash
git add backend/adapters/inference/brain_api_adapter.py backend/adapters/inference/vllm_adapter.py
git commit -m "chore: improve error visibility in inference adapters"
```
