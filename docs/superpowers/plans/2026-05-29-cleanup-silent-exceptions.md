# Cleanup Silent Exceptions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clean up all silent exceptions and potential silent fallback passes in fallback_adapter.py and qwen3_vl_adapter.py, and ensure structured logging/warnings are in place.

**Architecture:** Preserve the Hexagonal architecture and ensure robust logging. We replace silent `except` blocks with structured debug or warning logs.

**Tech Stack:** Python 3.10+, Pytest, Standard library `logging`

---

### Task 1: Clean up `fallback_adapter.py`

**Files:**
- Modify: `backend/adapters/inference/fallback_adapter.py`

- [ ] **Step 1: Replace silent exception handling in `_fallback_call`**
In `fallback_adapter.py`, locate the silent `except (InferenceNotImplementedError, NotImplementedError):` block in the `_fallback_call` method and replace it with a structured `logger.debug` log.

```python
            except (InferenceNotImplementedError, NotImplementedError) as e:
                logger.debug(
                    f"⚙️ [Fallback] {adapter.__class__.__name__}.{method_name} raised "
                    f"InferenceNotImplementedError/NotImplementedError (not implemented): {e}"
                )
                continue
```

- [ ] **Step 2: Verify the change compiles**
Run the pytest test suite to ensure that syntax and basic functionality are intact.

---

### Task 2: Clean up `qwen3_vl_adapter.py`

**Files:**
- Modify: `backend/adapters/inference/qwen3_vl_adapter.py`

- [ ] **Step 1: Replace silent ValueError fallback in `visual_rerank`**
In `qwen3_vl_adapter.py`, locate the silent `except ValueError:` in the `visual_rerank` method and replace it with a structured `logger.debug` log.

```python
                        if idx is None and "url" in item:
                            try:
                                idx = image_urls.index(item["url"])
                            except ValueError as e:
                                logger.debug(
                                    f"URL {item.get('url')} not found in image_urls list during Qwen3VL index lookup: {e}. "
                                    f"Falling back to index {i}."
                                )
                                idx = i
```

- [ ] **Step 2: Verify the changes compile**
Run the pytest test suite to ensure that syntax and basic functionality are intact.

---

### Task 3: Comprehensive Verification

- [ ] **Step 1: Run full suite of target tests**
Run:
```bash
.venv\Scripts\python -m pytest tests/core/test_fallback_adapter.py tests/core/test_qwen3_vl_adapter.py
```
Expected: PASS
