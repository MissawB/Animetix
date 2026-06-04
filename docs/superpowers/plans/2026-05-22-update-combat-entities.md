# Immersion 2.0 Entity Updates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update `CombatStats` and `CombatCharacter` Pydantic models to support character images and normalized power levels.

**Architecture:** Extend existing domain entities with new fields using Pydantic `Field` for validation and documentation.

**Tech Stack:** Python, Pydantic

---

### Task 1: Research and Preparation

**Files:**
- Modify: `backend/core/domain/entities/ai_schemas.py`

- [ ] **Step 1: Verify current file content**
Check that `CombatStats` and `CombatCharacter` are present and as expected.
Run: `grep -E "class (CombatStats|CombatCharacter)" backend/core/domain/entities/ai_schemas.py`

### Task 2: Update CombatStats Entity

**Files:**
- Modify: `backend/core/domain/entities/ai_schemas.py`
- Test: `tests/core/domain/entities/test_ai_schemas.py` (Create if missing)

- [ ] **Step 1: Create a test to verify the new field is required/optional**
Create `tests/core/domain/entities/test_ai_schemas_immersion.py` to test the updates.

```python
from backend.core.domain.entities.ai_schemas import CombatStats, CombatCharacter
import pytest

def test_combat_stats_tier_value():
    stats = CombatStats(
        tier="2-C",
        speed="MFTL+",
        durability="Multi-Galaxy",
        intelligence="Gifted",
        abilities=["Reality Warping"]
    )
    # Check default value
    assert stats.tier_value == 0
    
    # Check assignment
    stats_explicit = CombatStats(
        tier="2-C",
        speed="MFTL+",
        durability="Multi-Galaxy",
        intelligence="Gifted",
        abilities=["Reality Warping"],
        tier_value=85
    )
    assert stats_explicit.tier_value == 85
```

- [ ] **Step 2: Run the test and verify it fails**
Run: `pytest tests/core/domain/entities/test_ai_schemas_immersion.py`
Expected: `AttributeError` or `ValidationError` because `tier_value` doesn't exist.

- [ ] **Step 3: Update `CombatStats` in `backend/core/domain/entities/ai_schemas.py`**
Add `tier_value: int = Field(default=0, description="Normalized power scale (0-100)")`.

- [ ] **Step 4: Run the test and verify it passes**
Run: `pytest tests/core/domain/entities/test_ai_schemas_immersion.py`

### Task 3: Update CombatCharacter Entity

**Files:**
- Modify: `backend/core/domain/entities/ai_schemas.py`
- Test: `tests/core/domain/entities/test_ai_schemas_immersion.py`

- [ ] **Step 1: Add test for image_url**

```python
def test_combat_character_image_url():
    stats = CombatStats(tier="2-C", speed="X", durability="Y", intelligence="Z")
    char = CombatCharacter(
        name="Test Hero",
        wiki_url="https://example.com",
        stats=stats,
        summary="A test hero"
    )
    # Check default value
    assert char.image_url is None
    
    # Check assignment
    char_with_img = CombatCharacter(
        name="Test Hero",
        wiki_url="https://example.com",
        stats=stats,
        summary="A test hero",
        image_url="https://example.com/img.png"
    )
    assert char_with_img.image_url == "https://example.com/img.png"
```

- [ ] **Step 2: Run the test and verify it fails**
Run: `pytest tests/core/domain/entities/test_ai_schemas_immersion.py`

- [ ] **Step 3: Update `CombatCharacter` in `backend/core/domain/entities/ai_schemas.py`**
Add `image_url: Optional[str] = Field(default=None, description="URL of the character portrait")`.

- [ ] **Step 4: Run the test and verify it passes**
Run: `pytest tests/core/domain/entities/test_ai_schemas_immersion.py`

### Task 4: Final Validation and Commit

- [ ] **Step 1: Run all tests in the project to ensure no regressions**
Run: `pytest tests/`

- [ ] **Step 2: Commit changes**
Run:
```bash
git add backend/core/domain/entities/ai_schemas.py
git commit -m "feat(domain): update combat entities for immersion 2.0"
```
