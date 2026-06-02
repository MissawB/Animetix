# Core Domain Error Handling Refactoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finalize refactoring of error handling in Core Domain services using specific exception classes, implementing JSON retry logic, and structured logging.

**Architecture:** 
- Centralized exception handling using `AnimetixBaseError` subclasses.
- Self-healing JSON parsing in `LLMService`.
- Fail-safe state transitions in `AgenticRAGService`.
- Structured logging with rich context.

**Tech Stack:** Python, Pydantic, orjson, OpenTelemetry (optional/existing).

---

### Task 1: LLMService - Structured Generation & Retry Logic

**Files:**
- Modify: `backend/core/domain/services/llm_service.py`
- Test: `tests/backend/unit/services/test_llm_service_error_handling.py`

- [ ] **Step 1: Update imports and add ParsingError to LLMService**
- [ ] **Step 2: Update `generate` method to use structured logging and specific errors**
- [ ] **Step 3: Implement `generate_structured` method**
```python
def generate_structured(self, prompt, schema, system_prompt="", use_slm=False):
    res = self.generate(prompt, system_prompt, use_slm=use_slm)
    try:
        return self._parse_json(res, schema)
    except ParsingError as e:
        return self._retry_json(prompt, res, str(e), schema, system_prompt, use_slm)
```
- [ ] **Step 4: Implement `_parse_json` and `_retry_json` helpers**
- [ ] **Step 5: Write unit tests for JSON retry logic**
- [ ] **Step 6: Run tests and verify**
- [ ] **Step 7: Commit**

### Task 2: AdvancedRAGService - Surgical Error Refactoring

**Files:**
- Modify: `backend/core/domain/services/advanced_rag_service.py`
- Test: `tests/backend/unit/services/test_advanced_rag_error_handling.py`

- [ ] **Step 1: Replace generic `except Exception` in `hybrid_search`**
- [ ] **Step 2: Replace generic `except Exception` in `graph_rag_summaries`**
- [ ] **Step 3: Replace generic `except Exception` in `rerank_results`**
- [ ] **Step 4: Replace generic `except Exception` in `self_rag_verify`**
- [ ] **Step 5: Add structured context to all logger calls**
- [ ] **Step 6: Verify with existing tests and new unit tests**
- [ ] **Step 7: Commit**

### Task 3: AgenticRAGService - Robust State Machine & Failsafe

**Files:**
- Modify: `backend/core/domain/services/agentic_rag_service.py`
- Test: `tests/backend/unit/services/test_agentic_rag_failsafe.py`

- [ ] **Step 1: Update the main loop to specifically catch `InferenceTimeoutError`**
- [ ] **Step 2: Ensure timeout handling triggers `RAGState.FALLBACK_RAG`**
- [ ] **Step 3: Update all state handlers (`_handle_plan`, `_handle_research`, etc.) with structured logging**
- [ ] **Step 4: Update `_extract_json` to use the new `ParsingError` correctly**
- [ ] **Step 5: Write unit test simulating a timeout in `_handle_research`**
- [ ] **Step 6: Verify the service fails over to `FALLBACK_RAG` instead of crashing**
- [ ] **Step 7: Commit**

### Task 4: Final Integration & Verification

- [ ] **Step 1: Run all core service tests**
- [ ] **Step 2: Verify no regressions in existing RAG workflows**
- [ ] **Step 3: Final commit and cleanup**
