# Manga OCR SOTA 2026 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a high-precision Manga OCR pipeline using `dots.mocr` (Primary SOTA) and `manga-ocr` (Stable Fallback) via Hugging Face Inference API.

**Architecture:** 
1. Create `MangaOcrAdapter` implementing `InferencePort`.
2. Implement dual-strategy logic: `dots.mocr` for layout/styling, `manga-ocr` for raw Japanese extraction.
3. Update `MangaFlowService` to utilize these new capabilities.

**Tech Stack:** Python 3.10+, `huggingface_hub`, `Pillow` (for image processing).

---

### Task 1: Create MangaOcrAdapter

**Files:**
- Create: `backend/adapters/inference/manga_ocr_adapter.py`
- Test: `tests/core/test_manga_ocr_adapter.py`

- [ ] **Step 1: Write the failing test for Manga OCR**
```python
import pytest
from unittest.mock import MagicMock, patch
from adapters.inference.manga_ocr_adapter import MangaOcrAdapter

@patch("adapters.inference.manga_ocr_adapter.InferenceClient")
def test_manga_ocr_calls_hf_api(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    # Mock dots.mocr response
    mock_client.post.return_value = b'{"generated_text": "こんにちは"}'
    
    adapter = MangaOcrAdapter(token="fake_token")
    result = adapter.process_manga_page(b"fake_image_data")
    
    assert "こんにちは" in result["text"]
    assert result["model"] == "dots.mocr"
```

- [ ] **Step 2: Implement MangaOcrAdapter**
```python
import logging
import json
from typing import List, Dict, Any, Optional
from core.ports.inference_port import InferencePort
from huggingface_hub import InferenceClient

logger = logging.getLogger("animetix.inference.manga_ocr")

class MangaOcrAdapter(InferencePort):
    def __init__(self, token: str = None):
        self.client = InferenceClient(token=token)
        self.primary_model = "rednote-hilab/dots.mocr"
        self.fallback_model = "kha-white/manga-ocr-base"

    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]:
        """
        Processes a manga page using dots.mocr for layout and text.
        """
        try:
            # SOTA 2026: dots.mocr uses a specific document-parsing endpoint
            response = self.client.post(
                data=image_data,
                model=self.primary_model,
                headers={"Content-Type": "image/png"}
            )
            res_data = json.loads(response.decode("utf-8"))
            return {
                "text": res_data.get("generated_text", ""),
                "layout": res_data.get("layout", []),
                "model": "dots.mocr"
            }
        except Exception as e:
            logger.warning(f"dots.mocr failed, falling back to manga-ocr: {e}")
            return self._fallback_manga_ocr(image_data)

    def _fallback_manga_ocr(self, image_data: bytes) -> Dict[str, Any]:
        try:
            response = self.client.post(
                data=image_data,
                model=self.fallback_model,
                headers={"Content-Type": "image/png"}
            )
            res_data = json.loads(response.decode("utf-8"))
            return {
                "text": res_data.get("generated_text", ""),
                "layout": [],
                "model": "manga-ocr"
            }
        except Exception as e:
            logger.error(f"Manga OCR Fallback failed: {e}")
            return {"text": "", "layout": [], "error": str(e)}

    # Stub other InferencePort methods...
    def generate(self, prompt, system_prompt="", thinking_budget=0): return ""
```

- [ ] **Step 3: Commit**
```bash
git add backend/adapters/inference/manga_ocr_adapter.py tests/core/test_manga_ocr_adapter.py
git commit -m "feat: add MangaOcrAdapter with dots.mocr and fallback"
```

---

### Task 2: Inject and Connect MangaFlowService

**Files:**
- Modify: `backend/api/animetix/containers.py`
- Modify: `backend/core/domain/services/creative/manga_flow.py`

- [ ] **Step 1: Register MangaOcrAdapter in Container**
```python
    @property
    def manga_ocr_adapter(self):
        from adapters.inference.manga_ocr_adapter import MangaOcrAdapter
        return self._get('manga_ocr_adapter', lambda: MangaOcrAdapter(token=os.getenv("HF_TOKEN")))
```

- [ ] **Step 2: Update MangaFlowService to use the new adapter**
Update `manga_flow_service` property in `Container` to inject `self.manga_ocr_adapter` into `MangaFlowService`.

- [ ] **Step 3: Refactor MangaFlowService to handle rich OCR data**
Update `translate_manga_page` in `manga_flow.py` to use the `layout` data from `dots.mocr` for better text bubble inpainting.

- [ ] **Step 4: Commit**
```bash
git add backend/api/animetix/containers.py backend/core/domain/services/creative/manga_flow.py
git commit -m "chore: connect MangaFlowService to SOTA OCR adapter"
```
