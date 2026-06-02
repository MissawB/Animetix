# Clean up MangaOCRAdapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all `NotImplementedError` from `MangaOCRAdapter` and replace them with silent fallbacks and logging to ensure it conforms to `InferencePort` without crashing.

**Architecture:** The adapter will use a common `_log_not_implemented` helper method to log calls to unimplemented methods and return appropriate default values based on the `InferencePort` interface.

**Tech Stack:** Python, Logging

---

### Task 1: Research and Setup

**Files:**
- Modify: `backend/adapters/inference/manga_ocr_adapter.py`

- [ ] **Step 1: Verify current state**
    Read the file and identify all `NotImplementedError` occurrences.

### Task 2: Implement logging helper and replace NotImplementedError

**Files:**
- Modify: `backend/adapters/inference/manga_ocr_adapter.py`

- [ ] **Step 1: Add helper method and replace errors**

Replace all `NotImplementedError` with calls to a logging helper and return default values.

```python
    def _log_not_implemented(self, method_name: str):
        logger.warning(f"Method '{method_name}' is not implemented in MangaOCRAdapter and returns a default value.")

    def translate_manga_page(self, image_data: bytes, target_lang: str = "Français") -> Dict[str, Any]:
        self._log_not_implemented("translate_manga_page")
        return {}

    def generate(
        self, 
        prompt: str, 
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False
    ) -> str:
        self._log_not_implemented("generate")
        return ""

    def stream_generate(
        self, 
        prompt: str, 
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False
    ):
        self._log_not_implemented("stream_generate")
        return iter([])

    def calculate_visual_similarity(self, *args, **kwargs) -> float:
        self._log_not_implemented("calculate_visual_similarity")
        return 0.0

    def get_image_embedding(self, *args, **kwargs) -> List[float]:
        self._log_not_implemented("get_image_embedding")
        return []

    def classify_image(self, *args, **kwargs) -> Dict[str, float]:
        self._log_not_implemented("classify_image")
        return {}

    def detect_objects(self, *args, **kwargs) -> List[Dict]:
        self._log_not_implemented("detect_objects")
        return []

    def get_video_temporal_embeddings(self, *args, **kwargs) -> List[Dict[str, Any]]:
        self._log_not_implemented("get_video_temporal_embeddings")
        return []

    def localize_video_actions(self, *args, **kwargs) -> List[Dict[str, Any]]:
        self._log_not_implemented("localize_video_actions")
        return []

    def transform_image_to_anime(self, *args, **kwargs) -> str:
        self._log_not_implemented("transform_image_to_anime")
        return ""

    def transform_video_to_anime(self, *args, **kwargs) -> str:
        self._log_not_implemented("transform_video_to_anime")
        return ""

    def generate_soundscape(self, *args, **kwargs) -> str:
        self._log_not_implemented("generate_soundscape")
        return ""

    def clone_voice(self, *args, **kwargs) -> bytes:
        self._log_not_implemented("clone_voice")
        return b""

    def speech_to_speech(self, *args, **kwargs) -> bytes:
        self._log_not_implemented("speech_to_speech")
        return b""

    def inpaint_text_bubbles(self, *args, **kwargs) -> str:
        self._log_not_implemented("inpaint_text_bubbles")
        return ""

    def generate_image_description(self, *args, **kwargs) -> str:
        self._log_not_implemented("generate_image_description")
        return ""

    def get_diagnostics(self, *args, **kwargs) -> Dict[str, Any]:
        self._log_not_implemented("get_diagnostics")
        return {}

    def calculate_uncertainty(self, *args, **kwargs) -> Dict[str, float]:
        self._log_not_implemented("calculate_uncertainty")
        return {}

    def estimate_depth(self, *args, **kwargs) -> bytes:
        self._log_not_implemented("estimate_depth")
        return b""

    def generate_3d_scene(self, *args, **kwargs) -> Dict[str, Any]:
        self._log_not_implemented("generate_3d_scene")
        return {}

    def visual_rerank(self, *args, **kwargs) -> List[Dict[str, Any]]:
        self._log_not_implemented("visual_rerank")
        return []

    def get_multimodal_late_interaction(self, *args, **kwargs) -> List[List[float]]:
        self._log_not_implemented("get_multimodal_late_interaction")
        return []
    
    def moderate_content(self, *args, **kwargs) -> Dict[str, Any]:
        self._log_not_implemented("moderate_content")
        return {}

    def generate_image(self, *args, **kwargs) -> str:
        self._log_not_implemented("generate_image")
        return ""
```

### Task 3: Verification

- [ ] **Step 1: Check compilation**
    Run a simple python check to ensure no syntax errors.
    Command: `python -m py_compile backend/adapters/inference/manga_ocr_adapter.py`

- [ ] **Step 2: Commit changes**
    ```bash
    git add backend/adapters/inference/manga_ocr_adapter.py
    git commit -m "refactor: replace NotImplementedError with silent fallbacks in MangaOCRAdapter"
    ```
