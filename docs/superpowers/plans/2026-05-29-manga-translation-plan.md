# Plan d'Implémentation - Traduction de Manga (Chantier D)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mettre en place un pipeline robuste de Traduction de Manga avec un repli algorithmique local via Pillow si le GPU/modèle d'inpainting SDXL-Turbo n'est pas disponible, et corriger la suite de tests associée.

**Architecture:** Injecter l'adaptateur de repli central `FallbackInferenceAdapter` dans `MangaFlowService` au lieu de l'adaptateur OCR pur. Modifier `DiffusersAdapter` pour intercepter l'absence de GPU ou d'initialisation de pipeline neuronal, et basculer sur un dessin géométrique par Pillow (rectangle blanc et texte noir). Stabiliser la suite de tests en corrigeant les chemins de mock erronés.

**Tech Stack:** Python 3.12, Django 5.2, Pillow (PIL), Pytest, Dependency Injector, Hugging Face Transformers.

---

### Task 1 : Réalignement de l'injection de dépendances (DI)

**Files:**
- Modify: `backend/api/animetix/containers/core_services.py:225-231`
- Test: `tests/backend/api/test_temp.py` (ou créer un test rapide)

- [ ] **Step 1: Write a test verifying MangaFlowService's engine wiring**

Create/Modify `tests/core/test_manga_flow_di.py` :
```python
import pytest
from backend.api.animetix.containers.core_services import get_container
from backend.adapters.inference.fallback_adapter import FallbackInferenceAdapter

def test_manga_flow_service_wires_fallback_engine():
    # Load real container
    from animetix.api.dependencies import get_container
    container = get_container()
    manga_service = container.manga_flow_service()
    
    # Assert that the injected engine is FallbackInferenceAdapter (the central engine)
    assert isinstance(manga_service.inference_engine, FallbackInferenceAdapter)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\pytest tests/core/test_manga_flow_di.py -v`
Expected: FAIL with `AssertionError: assert isinstance(MangaOCRAdapter, FallbackInferenceAdapter)`

- [ ] **Step 3: Modify container config to inject fallback engine**

In `backend/api/animetix/containers/core_services.py`, replace lines 225-230 with:
```python
    manga_flow_service = providers.Singleton(
        MangaFlowService,
        inference_engine=inference.inference_engine,
        llm_service=agentic.llm_service,
        prompt_manager=infrastructure.prompt_manager
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\pytest tests/core/test_manga_flow_di.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/animetix/containers/core_services.py tests/core/test_manga_flow_di.py
git commit -m "chore(di): inject fallback inference_engine into manga_flow_service"
```

---

### Task 2 : Implémentation du Fallback Pillow local dans `DiffusersAdapter`

**Files:**
- Modify: `backend/adapters/inference/diffusers_adapter.py:240-301`
- Test: `tests/adapters/test_diffusers_adapter.py`

- [ ] **Step 1: Write the failing test for Pillow-only fallback**

Add a test method in `tests/adapters/test_diffusers_adapter.py` :
```python
import pytest
from unittest.mock import MagicMock
from backend.adapters.inference.diffusers_adapter import DiffusersAdapter

def test_inpaint_text_bubbles_pillow_fallback_when_pipe_none():
    # Instantiate DiffusersAdapter without loading pipelines (so pipe remains None)
    adapter = DiffusersAdapter(model_id="stabilityai/sdxl-turbo", use_fp16=False)
    adapter._inpaint_pipe = None  # Ensure it is None to trigger fallback
    
    # Create simple 10x10 black image bytes
    from PIL import Image
    from io import BytesIO
    img = Image.new("RGB", (100, 100), "black")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    image_bytes = buf.getvalue()
    
    # Run inpaint with standard parameters
    bubbles = [{"bbox": [10, 10, 90, 90], "text": "TEST"}]
    result = adapter.inpaint_text_bubbles(image_bytes, bubbles)
    
    # Check that a valid base64 image URL is returned
    assert result.startswith("data:image/jpeg;base64,")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\pytest tests/adapters/test_diffusers_adapter.py::test_inpaint_text_bubbles_pillow_fallback_when_pipe_none -v`
Expected: FAIL with `"Erreur: Modèle d'inpainting non chargé."` (current implementation returns string instead of processing fallback)

- [ ] **Step 3: Implement the PIL-only fallback flow**

Modify `inpaint_text_bubbles` in `backend/adapters/inference/diffusers_adapter.py` (lines 240-301) to support Pillow fallback :
```python
    def inpaint_text_bubbles(self, image_data: bytes, bubbles: List[Dict]) -> str:
        """
        Nettoie les bulles de texte via inpainting (SDXL) ou par repli algorithmique local (Pillow).
        """
        import base64
        from PIL import ImageDraw, ImageFont
        try:
            init_image = Image.open(BytesIO(image_data)).convert("RGB")
            width, height = init_image.size
            
            # Tente de charger le modèle d'inpainting neuronal
            try:
                self._load_inpainting()
            except Exception as load_err:
                logger.warning(f"⚠️ SDXL Inpainting loading failed: {load_err}. Falling back to Pillow-only rendering.")
            
            # --- Cas 1 : SDXL Inpainting Neuronal Disponible ---
            if self._inpaint_pipe is not None:
                mask_image = Image.new("L", (width, height), 0)
                draw_mask = ImageDraw.Draw(mask_image)
                for bubble in bubbles:
                    bbox = bubble.get('bbox')
                    if bbox:
                        draw_mask.rectangle(bbox, fill=255)
                
                num_steps = 4 if "turbo" in self.model_id.lower() else 25
                inpainted_image = self._inpaint_pipe(
                    prompt="clean manga bubble, no text, white background",
                    image=init_image,
                    mask_image=mask_image,
                    num_inference_steps=num_steps
                ).images[0]
            
            # --- Cas 2 : Fallback Pillow Algorithmique Local (CUDA indisponible / CPU) ---
            else:
                logger.info("🎨 Rendering manga text bubbles using robust Pillow fallback.")
                inpainted_image = init_image.copy()
                draw_fallback = ImageDraw.Draw(inpainted_image)
                for bubble in bubbles:
                    bbox = bubble.get('bbox') # [x1, y1, x2, y2]
                    if bbox:
                        # Dessiner un rectangle blanc opaque pour effacer le texte d'origine
                        draw_fallback.rectangle(bbox, fill="white")
            
            # --- Rendu commun du nouveau texte par-dessus la zone propre ---
            draw_final = ImageDraw.Draw(inpainted_image)
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except Exception:
                font = ImageFont.load_default()

            for bubble in bubbles:
                bbox = bubble.get('bbox')
                text = bubble.get('text')
                if bbox and text:
                    x1, y1, x2, y2 = bbox
                    t_bbox = draw_final.textbbox((0, 0), text, font=font)
                    t_w, t_h = t_bbox[2] - t_bbox[0], t_bbox[3] - t_bbox[1]
                    pos_x = (x1 + x2) / 2 - t_w / 2
                    pos_y = (y1 + y2) / 2 - t_h / 2
                    draw_final.text((pos_x, pos_y), text, fill="black", font=font)

            # Enregistrement et encodage base64
            buffered = BytesIO()
            inpainted_image.save(buffered, format="JPEG", quality=85)
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            self._log_usage(engine=f"diffusers:{self.model_id}:inpaint" if self._inpaint_pipe else "pillow:local:inpaint", units=1)
            return f"data:image/jpeg;base64,{img_str}"

        except Exception as e:
            logger.error(f"❌ Inpaint Text Bubbles failed: {e}")
            return f"Erreur: {e}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\pytest tests/adapters/test_diffusers_adapter.py::test_inpaint_text_bubbles_pillow_fallback_when_pipe_none -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/adapters/inference/diffusers_adapter.py tests/adapters/test_diffusers_adapter.py
git commit -m "feat(manga): implement robust PIL-only fallback for text bubble inpainting"
```

---

### Task 3 : Restabilisation de la Suite de Tests (Mocks)

**Files:**
- Modify: `tests/core/test_manga_ocr_adapter.py:13`
- Modify: `tests/adapters/test_fallback_structured.py:106`

- [ ] **Step 1: Check existing test failures**

Run: `.venv\Scripts\pytest tests/core/test_manga_ocr_adapter.py tests/adapters/test_fallback_structured.py -v`
Expected: FAIL due to ModuleNotFoundError/AttributeError on `src.adapters...`

- [ ] **Step 2: Correct mock targets in test files**

In `tests/core/test_manga_ocr_adapter.py`, replace line 13:
```python
        with patch('adapters.inference.manga_ocr_adapter.pipeline'):
```

In `tests/adapters/test_fallback_structured.py`, replace line 106:
```python
    with patch("adapters.inference.fallback_adapter.logger.error") as mock_log_err:
```

- [ ] **Step 3: Run the tests to verify they pass**

Run: `.venv\Scripts\pytest tests/core/test_manga_ocr_adapter.py tests/adapters/test_fallback_structured.py -v`
Expected: PASS

- [ ] **Step 4: Run the central manga_flow test to verify full pipeline passes**

Run: `.venv\Scripts\pytest tests/core/test_creative_vision_services.py -k test_translate_manga_page -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/core/test_manga_ocr_adapter.py tests/adapters/test_fallback_structured.py
git commit -m "test(manga): fix absolute mock patch targets to adapters namespace"
```
