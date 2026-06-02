# Real Drift Calculation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect `ArchetypeDriftService` to real user data sources (feedback, gameplay, and creative history) to calculate personalized archetype drift.

**Architecture:** The service will aggregate signals from three ports, use keyword matching to score archetypes from `ARCHETYPE_VISUAL_MAP`, and determine the dominant archetype for visual personalization.

**Tech Stack:** Python, Dependency Injector, Pydantic

---

### Task 1: Update ArchetypeDriftService Interface

**Files:**
- Modify: `backend/core/domain/services/archetype_drift_service.py`

- [ ] **Step 1: Update `__init__` to accept `repository`**

Modify `__init__` to accept `repository` and store it.

```python
class ArchetypeDriftService:
    def __init__(self, feedback_port, memory_service, repository):
        self.feedback_port = feedback_port
        self.memory_service = memory_service
        self.repository = repository
```

- [ ] **Step 2: Update `calculate_drift` to aggregate signals**

Implement the logic to fetch history and score archetypes.

```python
    def calculate_drift(self, user_id: int) -> VisualConfig:
        # Default fallback
        default_config = VisualConfig(
            archetype_id="default",
            primary_accent="#FD7706",
            aura_type="none",
            aura_intensity=0.0,
            font_vibe="default"
        )
        
        if not user_id: return default_config

        scores = {archetype: 0.0 for archetype in ARCHETYPE_VISUAL_MAP.keys()}
        
        # 1. Fetch Feedback signals
        feedbacks = self.feedback_port.get_user_feedback(user_id)
        for fb in feedbacks:
            if fb.get("is_positive"):
                context = (fb.get("input_context", "") + " " + fb.get("output_text", "")).lower()
                for arch in scores.keys():
                    if arch in context:
                        scores[arch] += 1.0

        # 2. Fetch Gameplay signals
        gameplay = self.repository.get_user_gameplay_history(user_id)
        for session in gameplay:
            target = session.get("target", "").lower()
            for arch in scores.keys():
                if arch in target:
                    scores[arch] += 1.0

        # 3. Fetch Creative signals
        creative = self.repository.get_user_creative_history(user_id)
        for fusion in creative:
            art_style = fusion.get("art_style", "").lower()
            for arch in scores.keys():
                if arch in art_style:
                    scores[arch] += 1.0

        # 4. Select dominant archetype
        total_score = sum(scores.values())
        if total_score == 0:
            return default_config
            
        dominant = max(scores, key=scores.get)
        vibe = ARCHETYPE_VISUAL_MAP.get(dominant, {})
        
        # Normalize intensity (max 1.0)
        intensity = min(1.0, scores[dominant] / (total_score if total_score > 0 else 1))
        
        return VisualConfig(
            archetype_id=dominant,
            primary_accent=vibe.get("primary_accent", "#FD7706"),
            aura_type=vibe.get("aura_type", "none"),
            aura_intensity=intensity,
            font_vibe=vibe.get("font_vibe", "default")
        )
```

- [ ] **Step 3: Commit changes**

```bash
git add backend/core/domain/services/archetype_drift_service.py
git commit -m "feat(personalization): update ArchetypeDriftService with real signal aggregation"
```

### Task 2: Update Container Registration

**Files:**
- Modify: `backend/api/animetix/containers/core_services.py`

- [ ] **Step 1: Inject repository into archetype_drift_service**

```python
    archetype_drift_service = providers.Singleton(
        ArchetypeDriftService,
        feedback_port=persistence.feedback_adapter,
        memory_service=agentic.memory_service,
        repository=persistence.repository
    )
```

- [ ] **Step 2: Commit changes**

```bash
git add backend/api/animetix/containers/core_services.py
git commit -m "refactor(di): inject repository into ArchetypeDriftService"
```

### Task 3: Verification

- [ ] **Step 1: Verify with existing tests (if any) or add a smoke test**

Run: `pytest tests/backend/core/test_archetype_drift.py`

- [ ] **Step 2: If tests fail due to missing repository in constructor, fix them**

Modify `tests/backend/core/test_archetype_drift.py` to provide a mock repository.

- [ ] **Step 3: Commit verification changes**

```bash
git add tests/backend/core/test_archetype_drift.py
git commit -m "test: update ArchetypeDriftService tests for new dependency"
```
