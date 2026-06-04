# Design Spec: Inference Adapters Cleanup

**Date:** 2025-05-14
**Status:** Approved (Auto-mode)

## 1. Goal
Remove redundant and placeholder methods from inference adapters to delegate non-implemented functionality to `InferencePort` base class.

## 2. Approach
For each adapter, identify methods that:
- Raise `NotImplementedError` or `InferenceNotImplementedError`.
- Return "empty" literals: `""`, `[]`, `{}`, `0.0`, `b""`, `None`.
- Only log a warning and return one of the above.
- Provide a redundant/inferior implementation of a base class default (e.g., `generate_structured`).

## 3. Targeted Adapters

### 3.1 LocalLlamaAdapter
- **Keep:** `__init__`, `_load_model`, `generate`, `stream_generate`, `health_check`.
- **Remove:** `calculate_visual_similarity`, `get_image_embedding`, `classify_image`, `detect_objects`, `get_video_temporal_embeddings`, `localize_video_actions`, `transform_image_to_anime`, `transform_video_to_anime`, `generate_soundscape`, `clone_voice`, `speech_to_speech`, `process_manga_page`, `translate_manga_page`, `inpaint_text_bubbles`, `generate_image_description`, `get_diagnostics`, `calculate_uncertainty`, `estimate_depth`, `generate_3d_scene`, `visual_rerank`, `moderate_content`, `get_multimodal_late_interaction`, `generate_image`.

### 3.2 TransformersAdapter
- **Keep:** Most methods as they have actual logic.
- **Remove:** `calculate_uncertainty`, `get_diagnostics`, `generate_image`, `generate_structured`.

### 3.3 MoondreamAdapter
- **Keep:** `__init__`, `_load_model`, `generate`, `stream_generate`, `generate_image_description`, `health_check`.
- **Remove:** `calculate_visual_similarity`, `get_image_embedding`, `classify_image`, `detect_objects`, `get_video_temporal_embeddings`, `localize_video_actions`, `transform_image_to_anime`, `transform_video_to_anime`, `generate_soundscape`, `clone_voice`, `speech_to_speech`, `estimate_depth`, `generate_3d_scene`, `process_manga_page`, `translate_manga_page`, `inpaint_text_bubbles`, `moderate_content`, `get_diagnostics`, `calculate_uncertainty`, `visual_rerank`, `get_multimodal_late_interaction`, `generate_image`.

### 3.4 Qwen3VLAdapter
- **Keep:** `__init__`, `localize_video_actions`, `generate`, `stream_generate`, `visual_rerank`, `health_check`.
- **Remove:** `calculate_visual_similarity`, `get_image_embedding`, `classify_image`, `detect_objects`, `get_video_temporal_embeddings`, `transform_image_to_anime`, `transform_video_to_anime`, `generate_soundscape`, `clone_voice`, `speech_to_speech`, `process_manga_page`, `translate_manga_page`, `inpaint_text_bubbles`, `moderate_content`, `generate_image_description`, `get_diagnostics`, `calculate_uncertainty`, `estimate_depth`, `generate_3d_scene`, `get_multimodal_late_interaction`, `generate_image`.

### 3.5 XTTSAdapter
- **Keep:** `__init__`, `_load_model`, `clone_voice`, `health_check`.
- **Remove:** All other placeholder methods using `*args, **kwargs`.

### 3.6 MangaOCRAdapter
- **Keep:** `__init__`, `process_manga_page`, `health_check`.
- **Remove:** `translate_manga_page`, `generate`, `stream_generate`, and all other placeholder methods. Also remove `_log_not_implemented` helper.

## 4. Verification
- Verify that each adapter still inherits correctly from `InferencePort`.
- Run basic instantiation tests for each adapter.
- Ensure no accidental removal of functional code in `TransformersAdapter`.
