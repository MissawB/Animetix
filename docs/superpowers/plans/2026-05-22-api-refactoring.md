# API Refactoring Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Splitting the monolithic `backend/api/animetix/api_views.py` into logical domain-specific modules.

**Architecture:** Create a package `backend/api/animetix/api/` and migrate views into `core.py`, `games.py`, `social.py`, and `labs.py`. Update `api_views.py` to act as a proxy for backward compatibility.

**Tech Stack:** Django, DRF, Python.

---

### Task 1: Migrate Core & Utils Views

**Files:**
- Create: `backend/api/animetix/api/core.py`
- Modify: `backend/api/animetix/api_views.py`

- [ ] **Step 1: Create core.py with base views**
Move `ConfigView`, `MediaSearchView`, `GameSessionView`, and `image_proxy_view` to `api/core.py`.

- [ ] **Step 2: Update api_views.py to import from core.py**
Remove the moved classes/functions from `api_views.py` and import them from `.api.core`.

- [ ] **Step 3: Verify core API endpoints**
Run: `python backend/api/manage.py check`
Expected: No system errors.

### Task 2: Migrate Game Views

**Files:**
- Create: `backend/api/animetix/api/games.py`
- Modify: `backend/api/animetix/api_views.py`

- [ ] **Step 1: Create games.py**
Move all game-related views (Classic, Akinetix, Emoji, Paradox, Vision, Blindtest, Covertest, Archetypist) to `api/games.py`.

- [ ] **Step 2: Update api_views.py**
Remove moved classes and import them from `.api.games`.

- [ ] **Step 3: Run existing tests**
Run: `pytest tests/core`
Expected: PASS.

### Task 3: Migrate Social & Profile Views

**Files:**
- Create: `backend/api/animetix/api/social.py`
- Modify: `backend/api/animetix/api_views.py`

- [ ] **Step 1: Create social.py**
Move `ProfileViewSet`, `CreativeFusionViewSet`, `SocialViewSet`, `AchievementViewSet`, `LeaderboardView`, `ProfileDetailView`, `MyCollectionView`, `NotificationListView`.

- [ ] **Step 2: Update api_views.py**
Remove moved classes and import from `.api.social`.

### Task 4: Migrate Labs & Data Views

**Files:**
- Create: `backend/api/animetix/api/labs.py`
- Modify: `backend/api/animetix/api_views.py`

- [ ] **Step 1: Create labs.py**
Move `DailyChallengeViewSet`, `LatentSpaceDataView`, `DailyChallengeDataView`, `CustomConfigDataView`, `TransparencyDataView`, `SpatialLabDataView`.

- [ ] **Step 2: Update api_views.py**
Remove moved classes and import from `.api.labs`.

- [ ] **Step 3: Final Verification**
Run: `python backend/api/manage.py check` and `pytest tests/backend` (if exists).
