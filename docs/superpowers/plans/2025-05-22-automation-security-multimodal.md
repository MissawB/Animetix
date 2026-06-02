# Automation Security & Multimodal Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Secure Celery tasks with locking, enhance the distillation pipeline with golden patterns, and expand multimodal capabilities in local adapters.

**Architecture:** 
- Distributed locking via Redis for tasks.
- File-based locking for local prompt persistence.
- LLM-driven pattern extraction from the Gold Dataset.
- Sliding window VLM analysis for video in GGUF.

**Tech Stack:** Python, Celery, Redis, Django, Transformers, llama-cpp-python, filelock.

---

### Task 1: Celery Task Locking

**Files:**
- Modify: `backend/api/animetix/tasks.py`

- [ ] **Step 1: Add Redis-based locking to `scheduled_dpo_optimization`**

```python
@shared_task
def scheduled_dpo_optimization():
    from django.core.cache import cache
    lock_id = "scheduled_dpo_optimization_lock"
    # Acquire lock for 1 hour (max task duration)
    if not cache.add(lock_id, "true", 3600):
        logger.warning("🤖 [DPO Task] Already running. Skipping.")
        return "Task already running."
    
    try:
        # Existing logic...
    finally:
        cache.delete(lock_id)
```

- [ ] **Step 2: Commit**

```bash
git add backend/api/animetix/tasks.py
git commit -m "feat: add redis lock to dpo optimization task"
```

### Task 2: PromptManager Resilience

**Files:**
- Modify: `backend/core/domain/services/prompt_manager.py`

- [ ] **Step 1: Add `filelock` to `update_system_prompt` and `add_few_shot_correction`**

```python
from filelock import FileLock, Timeout

# In update_system_prompt
lock_path = f"{overrides_path}.lock"
lock = FileLock(lock_path, timeout=5)
try:
    with lock:
        with open(overrides_path, 'w', encoding='utf-8') as f:
            yaml.dump(overrides, f, allow_unicode=True)
except Timeout:
    logger.error(f"Timeout acquiring lock for {overrides_path}")
except Exception as e:
    logger.error(f"Error saving overrides: {e}")
```

- [ ] **Step 2: Commit**

```bash
git add backend/core/domain/services/prompt_manager.py
git commit -m "fix: add file locking to PromptManager persistence"
```

### Task 3: Golden Pattern Extraction

**Files:**
- Modify: `backend/core/domain/services/distillation_pipeline.py`

- [ ] **Step 1: Implement `extract_golden_patterns`**

```python
def extract_golden_patterns(self, prompt_key: str) -> str:
    gold_path = "data/mlops/gold_dataset.json"
    if not os.path.exists(gold_path):
        return ""
    
    with open(gold_path, 'r', encoding='utf-8') as f:
        gold_data = json.load(f)
    
    # Filter relevant entries
    examples = [item for item in gold_data if item.get("prompt_key") == prompt_key][:5]
    if not examples:
        return ""
    
    analysis_prompt = f"Analyze these successful examples and extract the 'Golden Patterns' (style, structure, tone):\n{json.dumps(examples)}"
    patterns = self.teacher.generate(analysis_prompt, system_prompt="You are a Meta-Prompt Engineer.")
    return patterns
```

- [ ] **Step 2: Commit**

```bash
git add backend/core/domain/services/distillation_pipeline.py
git commit -m "feat: add golden pattern extraction to distillation pipeline"
```

### Task 4: GGUF Multimodal Expansion

**Files:**
- Modify: `backend/adapters/inference/gguf_adapter.py`

- [ ] **Step 1: Implement `localize_video_actions` and `_sample_video_frames`**

```python
def _sample_video_frames(self, video_data: bytes, max_frames: int = 8):
    # Same logic as TransformersAdapter using imageio
    ...

def localize_video_actions(self, video_data: bytes, action_queries: List[str]) -> List[Dict]:
    frames = self._sample_video_frames(video_data)
    results = []
    for query in action_queries:
        for i, frame in enumerate(frames):
            desc = self.generate_image_description(frame_bytes, f"Is the action '{query}' happening here? Answer YES or NO.")
            if "YES" in desc.upper():
                results.append({"action": query, "timestamp": i, "confidence": 0.8})
    return results
```

- [ ] **Step 2: Implement `generate_3d_scene` (Deterministic Fallback)**

```python
def generate_3d_scene(self, image_data: bytes, depth_map: bytes) -> Dict:
    # Point cloud projection logic from TransformersAdapter
    ...
```

- [ ] **Step 3: Commit**

```bash
git add backend/adapters/inference/gguf_adapter.py
git commit -m "feat: add video and 3d scene capabilities to GGUF adapter"
```
