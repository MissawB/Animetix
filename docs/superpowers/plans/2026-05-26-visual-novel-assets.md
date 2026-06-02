# Real-time Visual Engine (Sprites & BG) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a real-time visual engine for generating character sprites (with background removal) and background images for Visual Novels.

**Architecture:** Extend `DiffusersAdapter` with specialized sprite generation logic and implement `generate_scene_assets` in `VisualNovelService` to coordinate asset creation.

**Tech Stack:** Python, Diffusers (Stable Diffusion), PIL (Pillow) for image processing.

---

### Task 1: Extend `InferencePort` and `DiffusersAdapter` with `generate_sprite`

**Files:**
- Modify: `backend/core/ports/inference_port.py`
- Modify: `backend/adapters/inference/diffusers_adapter.py`
- Test: `tests/adapters/test_vn_visuals.py`

- [ ] **Step 1: Add `generate_sprite` to `InferencePort`**

```python
    def generate_sprite(self, prompt: str, style: str = "") -> str:
        """Génère un sprite de personnage (généralement sur fond transparent ou blanc)."""
        return self.generate_image(f"{prompt}, full body portrait on pure white background, anime character sheet style", style)
```

- [ ] **Step 2: Write the failing test for `generate_sprite` in `DiffusersAdapter`**

```python
import pytest
from unittest.mock import MagicMock, patch
from adapters.inference.diffusers_adapter import DiffusersAdapter

@pytest.fixture
def adapter():
    return DiffusersAdapter()

def test_generate_sprite_calls_generate_image_with_correct_prompt(adapter):
    with patch.object(adapter, 'generate_image', return_value="data:image/png;base64,fake") as mock_gen:
        res = adapter.generate_sprite("Naruto", style="manga")
        assert res == "data:image/png;base64,fake"
        mock_gen.assert_called_once()
        args, _ = mock_gen.call_args
        assert "full body portrait on pure white background, anime character sheet style" in args[0]
        assert "Naruto" in args[0]
        assert "manga" in args[1]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/adapters/test_vn_visuals.py`
Expected: FAIL (DiffusersAdapter has no attribute 'generate_sprite')

- [ ] **Step 3: Implement `generate_sprite` in `DiffusersAdapter`**

```python
    def generate_sprite(self, prompt: str, style: str = "") -> str:
        sprite_prompt = f"{prompt}, full body portrait on pure white background, anime character sheet style"
        image_data_url = self.generate_image(sprite_prompt, style)
        
        if image_data_url.startswith("data:image"):
            try:
                # Optional: Remove white background and make it transparent
                header, encoded = image_data_url.split(",", 1)
                img_data = base64.b64decode(encoded)
                img = Image.open(BytesIO(img_data)).convert("RGBA")
                
                # Simple white background removal
                datas = img.getdata()
                new_data = []
                for item in datas:
                    # If pixel is near white, make it transparent
                    if item[0] > 240 and item[1] > 240 and item[2] > 240:
                        new_data.append((255, 255, 255, 0))
                    else:
                        new_data.append(item)
                img.putdata(new_data)
                
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                return f"data:image/png;base64,{img_str}"
            except Exception as e:
                logger.error(f"❌ Sprite background removal failed: {e}")
                return image_data_url
        return image_data_url
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/adapters/test_vn_visuals.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/adapters/inference/diffusers_adapter.py tests/adapters/test_vn_visuals.py
git commit -m "feat: add generate_sprite to DiffusersAdapter"
```

### Task 2: Implement `generate_scene_assets` in `VisualNovelService`

**Files:**
- Modify: `backend/core/domain/services/creative/visual_novel_service.py`
- Modify: `backend/core/domain/services/llm_service.py` (to expose vision adapter)
- Test: `tests/adapters/test_vn_visuals.py`

- [ ] **Step 1: Update `LLMService` to provide access to vision adapter**
Check `backend/core/domain/services/llm_service.py` first.

- [ ] **Step 2: Write failing test for `generate_scene_assets`**

```python
from core.domain.services.creative.visual_novel_service import VisualNovelService
from core.domain.entities.ai_schemas import VNScene

def test_generate_scene_assets(adapter):
    # Mock LLMService and its vision engine
    mock_llm = MagicMock()
    mock_llm.vision_engine = adapter
    service = VisualNovelService(llm_service=mock_llm, repository=MagicMock())
    
    scene = VNScene(character="Goku", text="Hello", mood="Happy", bg_prompt="a sunny forest")
    
    with patch.object(adapter, 'generate_sprite', return_value="url_sprite") as m_sprite, \
         patch.object(adapter, 'generate_image', return_value="url_bg") as m_bg:
        
        assets = service.generate_scene_assets(scene, session_seed=42)
        
        assert assets["sprite_url"] == "url_sprite"
        assert assets["background_url"] == "url_bg"
        m_sprite.assert_called_once()
        m_bg.assert_called_once()
```

- [ ] **Step 3: Implement `generate_scene_assets` in `VisualNovelService`**

```python
    def generate_scene_assets(self, scene: VNScene, session_seed: int) -> dict:
        """Generates character sprite and background for a scene."""
        logger.info(f"Generating assets for scene with character: {scene.character}")
        
        # We need access to the image generation engine
        # Assuming llm_service has a reference to the vision/image engine
        engine = self.llm_service.vision_engine
        
        sprite_url = engine.generate_sprite(f"{scene.character}, {scene.mood} expression")
        bg_url = engine.generate_image(scene.bg_prompt)
        
        return {
            "sprite_url": sprite_url,
            "background_url": bg_url
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/adapters/test_vn_visuals.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/core/domain/services/creative/visual_novel_service.py backend/core/domain/services/llm_service.py
git commit -m "feat: implement generate_scene_assets in VisualNovelService"
```

### Task 3: Final Integration and Verification

- [ ] **Step 1: Run all tests in `tests/adapters/test_vn_visuals.py`**
- [ ] **Step 2: Verify consistency (manual check of logic)**
- [ ] **Step 3: Commit and Finish**
