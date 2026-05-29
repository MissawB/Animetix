# VS Battle Immersion 2.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enhance the VS Battle game with character images, visual power gauges, and a real-time debate animation.

**Architecture:** Extend existing Domain/Port/Adapter layers. Add frontend JavaScript for real-time visual effects.

**Tech Stack:** Python 3.10, Django, Pydantic, Tailwind CSS, Vanilla JavaScript.

---

### Task 1: Update Entities

**Files:**
- Modify: `backend/core/domain/entities/ai_schemas.py`

- [ ] **Step 1: Add image_url and tier_value to schemas**

```python
class CombatStats(BaseModel):
    tier: str = Field(description="Attack Potency Tier (e.g., 2-C)")
    tier_value: int = Field(default=0, description="Normalized power scale (0-100)")
    # ... other fields remain
```

- [ ] **Step 2: Commit Entities**
```bash
git add backend/core/domain/entities/ai_schemas.py
git commit -m "feat(domain): update combat entities for immersion 2.0"
```

---

### Task 2: Enhance FandomAdapter (Image Extraction)

**Files:**
- Modify: `backend/adapters/persistence/fandom_adapter.py`

- [ ] **Step 1: Implement image URL fetching**
Use `prop=pageimages` in MediaWiki API to get character portraits.

- [ ] **Step 2: Commit Adapter**
```bash
git add backend/adapters/persistence/fandom_adapter.py
git commit -m "feat(adapters): enhance FandomAdapter with image extraction"
```

---

### Task 3: Logic Update (Power Mapping)

**Files:**
- Modify: `backend/core/domain/services/creative/vs_battle_service.py`

- [ ] **Step 1: Implement `_map_tier_to_value` logic**
Create a mapping dictionary for VS Battles Wiki tiers (0, 1-A, 1-B, ... 10-C).

- [ ] **Step 2: Update parsing and orchestration**
Ensure `tier_value` and `image_url` are populated during character creation.

- [ ] **Step 3: Commit Logic**
```bash
git add backend/core/domain/services/creative/vs_battle_service.py
git commit -m "feat(domain): implement tier normalization and image handling in VsBattleService"
```

---

### Task 4: Frontend Immersion (Gauges & Typewriter)

**Files:**
- Modify: `backend/api/animetix/templates/animetix/games/vs_battle_result.html`

- [ ] **Step 1: Add dynamic gauges with Tailwind**
Use the `tier_value` to set the width of progress bars.

- [ ] **Step 2: Implement typewriter script**
Add a `<script>` section to animate the `debate_history` text.

- [ ] **Step 3: Commit UI**
```bash
git add backend/api/animetix/templates/animetix/games/vs_battle_result.html
git commit -m "feat(frontend): add power gauges and typewriter effect to VS Battle results"
```
