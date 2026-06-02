# Personalization Entities & Schema Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the domain entities and constants for the Hyper-Personnalisation Graphique feature in Animetix.

**Architecture:** Hexagonal Architecture - Domain layer. Entities defined using Pydantic for validation.

**Tech Stack:** Python, Pydantic, Pytest

---

### Task 1: Personalization Domain Entities

**Files:**
- Create: `backend/core/domain/entities/personalization.py`
- Create: `tests/core/domain/entities/test_personalization.py`

- [ ] **Step 1: Write the failing tests for Pydantic models**

```python
import pytest
from pydantic import ValidationError
from backend.core.domain.entities.personalization import VisualConfig, ArchetypeScore

def test_visual_config_valid():
    config = VisualConfig(
        archetype_id="shonen_hero",
        primary_accent="#FF4500",
        aura_type="fire",
        aura_intensity=0.8,
        font_vibe="brush"
    )
    assert config.archetype_id == "shonen_hero"
    assert config.aura_intensity == 0.8

def test_visual_config_invalid_intensity():
    with pytest.raises(ValidationError):
        VisualConfig(
            archetype_id="shonen_hero",
            primary_accent="#FF4500",
            aura_type="fire",
            aura_intensity=1.5,  # Out of range 0.0-1.0
            font_vibe="brush"
        )

def test_archetype_score_valid():
    score = ArchetypeScore(scores={"shonen_hero": 0.5, "cyberpunk": 0.2})
    assert score.scores["shonen_hero"] == 0.5
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/domain/entities/test_personalization.py`
Expected: FAIL (ModuleNotFoundError or ImportError)

- [ ] **Step 3: Implement VisualConfig and ArchetypeScore schemas**

```python
from pydantic import BaseModel, Field
from typing import Dict, Optional

class VisualConfig(BaseModel):
    archetype_id: str
    primary_accent: str
    aura_type: str  # "none", "fire", "electric", "shadow", "sparkles"
    aura_intensity: float = Field(ge=0.0, le=1.0)
    font_vibe: str  # "default", "manga", "brush"

class ArchetypeScore(BaseModel):
    scores: Dict[str, float]  # Map archetype name to current intensity
```

- [ ] **Step 4: Define the mapping constants**

```python
ARCHETYPE_VISUAL_MAP = {
    "shonen_hero": {
        "primary_accent": "#FF4500",
        "aura_type": "fire",
        "font_vibe": "brush"
    },
    "seinen_mystery": {
        "primary_accent": "#2F4F4F",
        "aura_type": "shadow",
        "font_vibe": "manga"
    },
    "cyberpunk": {
        "primary_accent": "#00FFFF",
        "aura_type": "electric",
        "font_vibe": "default"
    }
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/core/domain/entities/test_personalization.py`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/core/domain/entities/personalization.py tests/core/domain/entities/test_personalization.py
git commit -m "feat(personalization): add domain entities and schemas"
```
