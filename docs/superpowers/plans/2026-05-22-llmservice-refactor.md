# LLMService Refactoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate redundant token tracking logic and optimize forbidden terms filtering in `LLMService`.

**Architecture:** 
- Centralize token calculation into a private helper method `_get_token_usage`.
- Optimize forbidden terms filtering by combining them into a single case-insensitive regex.

**Tech Stack:** Python, `re`, `pydantic`.

---

### Task 1: Update Tests to match current LLMService interface

**Files:**
- Modify: `tests/core/test_llm_service.py`

- [ ] **Step 1: Update mocks in tests**

Modify `tests/core/test_llm_service.py` to return `InferenceResponse` objects.

```python
from core.domain.entities.ai_schemas import InferenceResponse, InferenceMetadata

# In test_generate_success
mock_engine.generate.return_value = InferenceResponse(text="Hello World")

# In test_generate_with_forbidden_terms
mock_engine.generate.return_value = InferenceResponse(text="Naruto is a ninja from Naruto series.")
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/core/test_llm_service.py`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/core/test_llm_service.py
git commit -m "test: update llm_service tests to use InferenceResponse"
```

### Task 2: Consolidate Token Tracking Logic

**Files:**
- Modify: `backend/core/domain/services/llm_service.py`
- Modify: `tests/core/test_llm_service.py`

- [ ] **Step 1: Add failing test for token tracking**

Add a test that verifies `log_usage` is called with correct tokens.

```python
def test_generate_logs_usage_correctly(llm_service, mock_engine):
    from core.ports.usage_port import UsagePort
    from core.domain.entities.ai_schemas import InferenceResponse, InferenceMetadata
    
    usage_port = MagicMock(spec=UsagePort)
    llm_service.usage_port = usage_port
    
    mock_engine.generate.return_value = InferenceResponse(
        text="Response",
        metadata=InferenceMetadata(usage={"prompt_tokens": 10, "completion_tokens": 5})
    )
    
    llm_service.generate("Prompt", "System")
    
    usage_port.log_usage.assert_called_once()
    args, kwargs = usage_port.log_usage.call_args
    assert kwargs['input_tokens'] == 10
    assert kwargs['output_tokens'] == 5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_llm_service.py::test_generate_logs_usage_correctly`

- [ ] **Step 3: Implement `_get_token_usage` and refactor `generate`**

In `backend/core/domain/services/llm_service.py`:

```python
    def _get_token_usage(self, response_obj: Any, prompt: str, system_prompt: str) -> tuple[int, int, int]:
        usage = response_obj.metadata.usage if response_obj.metadata else None
        if usage:
            in_tokens = usage.get("prompt_tokens", (len(prompt) + len(system_prompt)) // 4)
            out_tokens = usage.get("completion_tokens", len(response_obj.text) // 4)
            total_tokens = usage.get("total_tokens", in_tokens + out_tokens)
        else:
            in_tokens = (len(prompt) + len(system_prompt)) // 4
            out_tokens = len(response_obj.text) // 4
            total_tokens = in_tokens + out_tokens
        return in_tokens, out_tokens, total_tokens
```

Update `generate` to use it:

```python
            in_tokens, out_tokens, total_tokens = self._get_token_usage(response_obj, prompt, system_prompt)
            
            # --- W&B OBSERVABILITY ---
            if self.obs_service:
                model_id = getattr(engine, 'model_name', 'local-llama')
                self.obs_service.log_inference(model_id, latency, total_tokens, metadata={"slm": use_slm})

            # --- TOKEN TRACKING ---
            if self.usage_port:
                engine_name = getattr(engine, 'model_name', 'brain-api')
                if use_slm: engine_name += "-slm"
                self.usage_port.log_usage(engine_name, in_tokens, out_tokens, user_id=user_id)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_llm_service.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/core/domain/services/llm_service.py tests/core/test_llm_service.py
git commit -m "refactor: consolidate token tracking logic in LLMService"
```

### Task 3: Optimize Forbidden Terms Filtering

**Files:**
- Modify: `backend/core/domain/services/llm_service.py`
- Modify: `tests/core/test_llm_service.py`

- [ ] **Step 1: Add test case for multiple forbidden terms**

```python
def test_generate_with_multiple_forbidden_terms(llm_service, mock_engine):
    from core.domain.entities.ai_schemas import InferenceResponse
    mock_engine.generate.return_value = InferenceResponse(text="Naruto and Sasuke are friends.")
    res = llm_service.generate("Hi", forbidden_terms=["Naruto", "Sasuke"])
    assert "[CENSURÉ] and [CENSURÉ] are friends." in res
```

- [ ] **Step 2: Optimize implementation**

In `backend/core/domain/services/llm_service.py`:

```python
            # --- LLM GUARDRAILS (Sanitization) ---
            if forbidden_terms:
                import re
                valid_terms = [re.escape(t) for t in forbidden_terms if t]
                if valid_terms:
                    pattern = re.compile("|".join(valid_terms), re.IGNORECASE)
                    res = pattern.sub("[CENSURÉ]", res)
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `pytest tests/core/test_llm_service.py`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/core/domain/services/llm_service.py tests/core/test_llm_service.py
git commit -m "perf: optimize forbidden terms filtering in LLMService"
```
