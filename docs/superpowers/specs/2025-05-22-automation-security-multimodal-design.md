# Design Document: Automation Security & Multimodal Expansion

**Date:** 2025-05-22
**Topic:** Task locking, distillation patterns, and multimodal adapters

## 1. Architecture Overview

This design addresses three areas:
- **Concurrency & Resilience:** Preventing Celery task overlap and handling file access conflicts.
- **Knowledge Distillation:** Extracting high-level patterns from a Gold Dataset to improve system prompts.
- **Multimodal Inference:** Extending local adapters (GGUF/Transformers) with video and 3D scene capabilities.

## 2. Component Design

### 2.1. Celery Concurrency & Task Locking
We will implement a distributed lock using Redis to ensure that sensitive tasks like `scheduled_dpo_optimization` do not run concurrently.

- **Mechanism:** `django-redis` cache.
- **Implementation:** A decorator or a context manager inside `tasks.py` that uses `cache.add(lock_key, value, timeout)` for atomic locking.
- **Exception Handling in `PromptManager`:**
    - Use `filelock.FileLock` for writing to `auto_corrections.json` and `dpo_optimized_prompts.yaml`.
    - Catch `Timeout` and `IOError` to prevent task crashes, with logging and optional retries.

### 2.2. Golden Pattern Extraction & Injection
Enrich the `ModelDistillationPipeline` to leverage the `Gold Dataset` for meta-prompting.

- **`extract_golden_patterns(prompt_key)`**:
    - Load `data/mlops/gold_dataset.json`.
    - Filter entries relevant to the `prompt_key`.
    - Use the Teacher LLM to summarize the successful stylistic elements and structural patterns ("Golden Patterns").
- **`inject_patterns_to_prompts(prompt_key, patterns)`**:
    - Pass patterns to `PromptManager.update_system_prompt` or a new specialized method.
    - `PromptManager` will prepend these patterns to the system prompt to guide future generations.

### 2.3. Multimodal Capabilities (GGUF & Transformers)
- **`GgufAdapter`**:
    - Implement `_sample_video_frames` using `imageio` (similar to TransformersAdapter).
    - Implement `localize_video_actions`:
        - Loop through sampled frames.
        - Call `generate_image_description` for each frame with a query-specific prompt.
        - Aggregate results into a temporal timeline.
    - Implement `generate_3d_scene`:
        - Point cloud generation from depth map (fallback to deterministic logic if no specialized library).
- **`TransformersAdapter`**:
    - Refine existing implementations for robustness.
    - Ensure `localize_video_actions` uses the `Qwen2-VL` model correctly with the sliding window approach.

## 3. Data Flow

1. **Locking:** Task starts -> Redis Check -> Lock -> Execute -> Unlock.
2. **Distillation:** Gold Dataset -> Extract Patterns (LLM) -> Update PromptManager -> Persist YAML Overrides.
3. **Multimodal:** Video Buffer -> Sample Frames -> VLM Analysis -> JSON Result.

## 4. Testing Strategy

- **Concurrency:** Mock Redis `cache.add` to return `False` and verify task exits gracefully.
- **File Locks:** Unit test `PromptManager` with multiple threads attempting to write simultaneously.
- **Distillation:** Verify `extract_golden_patterns` returns a non-empty string when provided with valid gold data.
- **Multimodal:** Use small mock video buffers and verify the frame sampling logic.

## 5. Success Criteria

- No duplicate `scheduled_dpo_optimization` logs in the same timeframe.
- `dpo_optimized_prompts.yaml` contains "Golden Patterns" section.
- `GgufAdapter` can describe frames sampled from a video buffer.
