# Inference Adapters Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove redundant and placeholder methods from inference adapters in `backend/adapters/inference/` to delegate to `InferencePort` base class.

**Architecture:** Use inheritance and base class default implementations to handle non-supported features via `InferenceNotImplementedError`.

**Tech Stack:** Python, ABC.

---

### Task 1: Create Comprehensive Verification Script

**Files:**
- Create: `scripts/verify_adapters_cleanup.py`

- [ ] **Step 1: Write the verification script**

```python
import sys
import os
import logging
from typing import List

# Add src to path
sys.path.append(os.path.abspath("src"))

from core.ports.inference_port import InferencePort, InferenceNotImplementedError
from adapters.inference.local_llama_adapter import LocalLlamaAdapter
from adapters.inference.transformers_adapter import TransformersAdapter
from adapters.inference.moondream_adapter import MoondreamAdapter
from adapters.inference.qwen3_vl_adapter import Qwen3VLAdapter
from adapters.inference.xtts_adapter import XTTSAdapter
from adapters.inference.manga_ocr_adapter import MangaOCRAdapter

def test_adapter(adapter: InferencePort, adapter_name: str):
    print(f"\n--- Testing {adapter_name} ---")
    
    # These should be implemented and NOT raise NotImplementedError
    try:
        adapter.health_check()
        print(f"✅ {adapter_name}.health_check() implemented")
    except Exception as e:
        print(f"❌ {adapter_name}.health_check() failed: {e}")

    # This should raise InferenceNotImplementedError if removed correctly (and if not implemented)
    try:
        adapter.calculate_visual_similarity("test", "test", "test")
        print(f"⚠️ {adapter_name}.calculate_visual_similarity() returned a value (maybe implemented?)")
    except InferenceNotImplementedError:
        print(f"✅ {adapter_name}.calculate_visual_similarity() correctly delegates to base class (raises InferenceNotImplementedError)")
    except Exception as e:
        print(f"❌ {adapter_name}.calculate_visual_similarity() raised unexpected error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    adapters = [
        (LocalLlamaAdapter(model_path="mock"), "LocalLlamaAdapter"),
        (TransformersAdapter(), "TransformersAdapter"),
        (MoondreamAdapter(), "MoondreamAdapter"),
        (Qwen3VLAdapter(), "Qwen3VLAdapter"),
        (XTTSAdapter(), "XTTSAdapter"),
        (MangaOCRAdapter(), "MangaOCRAdapter"),
    ]
    
    for adapter, name in adapters:
        test_adapter(adapter, name)
```

- [ ] **Step 2: Run verification script**

Run: `python scripts/verify_adapters_cleanup.py`
Expected: Initially, many will NOT raise `InferenceNotImplementedError` because they return `0.0` or similar.

- [ ] **Step 3: Commit**

```bash
git add scripts/verify_adapters_cleanup.py
git commit -m "test: add verification script for inference adapters cleanup"
```

---

### Task 2: Cleanup LocalLlamaAdapter

**Files:**
- Modify: `backend/adapters/inference/local_llama_adapter.py`

- [ ] **Step 1: Remove all placeholder methods**

Remove all methods EXCEPT `__init__`, `_load_model`, `generate`, `stream_generate`, and `health_check`.

- [ ] **Step 2: Verify with script**

Run: `python scripts/verify_adapters_cleanup.py`
Expected: `LocalLlamaAdapter` now correctly delegates to base class.

- [ ] **Step 3: Commit**

```bash
git add backend/adapters/inference/local_llama_adapter.py
git commit -m "refactor: cleanup LocalLlamaAdapter redundant methods"
```

---

### Task 3: Cleanup TransformersAdapter

**Files:**
- Modify: `backend/adapters/inference/transformers_adapter.py`

- [ ] **Step 1: Remove redundant methods**

Remove `calculate_uncertainty`, `get_diagnostics`, `generate_image`, and `generate_structured`.

- [ ] **Step 2: Verify with script**

Run: `python scripts/verify_adapters_cleanup.py`
Expected: `TransformersAdapter` still has its many features but delegates the removed ones.

- [ ] **Step 3: Commit**

```bash
git add backend/adapters/inference/transformers_adapter.py
git commit -m "refactor: cleanup TransformersAdapter redundant methods"
```

---

### Task 4: Cleanup MoondreamAdapter

**Files:**
- Modify: `backend/adapters/inference/moondream_adapter.py`

- [ ] **Step 1: Remove placeholder methods**

Remove all methods EXCEPT `__init__`, `_load_model`, `generate`, `stream_generate`, `generate_image_description`, and `health_check`.

- [ ] **Step 2: Verify with script**

Run: `python scripts/verify_adapters_cleanup.py`

- [ ] **Step 3: Commit**

```bash
git add backend/adapters/inference/moondream_adapter.py
git commit -m "refactor: cleanup MoondreamAdapter redundant methods"
```

---

### Task 5: Cleanup Qwen3VLAdapter

**Files:**
- Modify: `backend/adapters/inference/qwen3_vl_adapter.py`

- [ ] **Step 1: Remove placeholder methods**

Remove all methods EXCEPT `__init__`, `localize_video_actions`, `generate`, `stream_generate`, `visual_rerank`, and `health_check`.

- [ ] **Step 2: Verify with script**

Run: `python scripts/verify_adapters_cleanup.py`

- [ ] **Step 3: Commit**

```bash
git add backend/adapters/inference/qwen3_vl_adapter.py
git commit -m "refactor: cleanup Qwen3VLAdapter redundant methods"
```

---

### Task 6: Cleanup XTTSAdapter

**Files:**
- Modify: `backend/adapters/inference/xtts_adapter.py`

- [ ] **Step 1: Remove placeholder methods**

Remove all methods EXCEPT `__init__`, `_load_model`, `clone_voice`, and `health_check`.

- [ ] **Step 2: Verify with script**

Run: `python scripts/verify_adapters_cleanup.py`

- [ ] **Step 3: Commit**

```bash
git add backend/adapters/inference/xtts_adapter.py
git commit -m "refactor: cleanup XTTSAdapter redundant methods"
```

---

### Task 7: Cleanup MangaOCRAdapter

**Files:**
- Modify: `backend/adapters/inference/manga_ocr_adapter.py`

- [ ] **Step 1: Remove placeholder methods and helper**

Remove `_log_not_implemented` and all methods EXCEPT `__init__`, `process_manga_page`, and `health_check`.

- [ ] **Step 2: Verify with script**

Run: `python scripts/verify_adapters_cleanup.py`

- [ ] **Step 3: Commit**

```bash
git add backend/adapters/inference/manga_ocr_adapter.py
git commit -m "refactor: cleanup MangaOCRAdapter redundant methods"
```
