# Complete Manga Flow and Spatial Computing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Functional implementation of Manga-OCR/Translation (Manga Flow) and 3D Gaussian Splatting (Spatial Computing) by removing stub logic and fixing adapter priorities.

**Architecture:** We are moving away from simulated/fake logic towards SOTA implementations. We prioritize specialized adapters (`MangaOCRAdapter` with LightonOCR) over generic ones and enforce the use of `gaussian_splatting` in the 3D pipeline.

**Tech Stack:** Python, Transformers (LightonOCR, Depth-Anything), Diffusers (SDXL-Turbo Inpainting), PIL, NumPy.

---

### Task 1: Fix Manga Flow Pipeline

**Files:**
- Modify: `backend/adapters/inference/manga_ocr.py`
- Modify: `backend/api/animetix/containers/inference.py`
- Modify: `backend/core/domain/services/creative/manga_flow.py`

- [ ] **Step 1: Remove fake simulated layout from `MangaOcrMixin`**
  It should return an error if it's just a handwritten OCR fallback that can't handle manga layout.

```python
    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]:
        """Generic fallback OCR - NO LONGER simulates manga layout."""
        # implementation...
        return {
            "text": extracted_text,
            "layout": [], # Empty layout as we don't know it
            "status": "partial_success"
        }
```

- [ ] **Step 2: Prioritize `MangaOCRAdapter` in DI Container**
  Move `manga_ocr_adapter` to the top of the `adapters` list in `FallbackInferenceAdapter`.

- [ ] **Step 3: Update `MangaFlowService` to handle missing layout gracefully**
  If `layout` is empty, use the whole image as a single bubble or show an error.

- [ ] **Step 4: Commit**

```bash
git add backend/adapters/inference/manga_ocr.py backend/api/animetix/containers/inference.py backend/core/domain/services/creative/manga_flow.py
git commit -m "feat: functional Manga Flow by prioritizing specialized OCR and removing fake layout simulation"
```

### Task 2: Functional 3D Spatial Computing

**Files:**
- Modify: `backend/core/domain/services/spatial_computing_service.py`
- Modify: `backend/adapters/inference/depth_estimation.py`

- [ ] **Step 1: Enforce Gaussian Splatting in `SpatialComputingService`**
  Pass `mode="gaussian_splatting"` to `generate_3d_scene`.

- [ ] **Step 2: Harden `generate_3d_splats` in `DepthEstimationMixin`**
  Ensure it uses the constants from `backend/core/constants.py` correctly.

- [ ] **Step 3: Commit**

```bash
git add backend/core/domain/services/spatial_computing_service.py backend/adapters/inference/depth_estimation.py
git commit -m "feat: upgrade Spatial Computing to SOTA 3D Gaussian Splatting by default"
```

### Task 3: Verify & Smoke Test

- [ ] **Step 1: Create a smoke test script for Manga Flow**
  `scripts/test_manga_flow.py`

- [ ] **Step 2: Create a smoke test script for 3D reconstruction**
  `scripts/test_3d_spatial.py`

- [ ] **Step 3: Commit**

```bash
git add scripts/test_manga_flow.py scripts/test_3d_spatial.py
git commit -m "test: add smoke tests for Manga Flow and 3D Spatial Computing"
```
