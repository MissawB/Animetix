# World Boss / Global Boss UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a communal Raid Boss system where users participate in a global challenge to defeat a "World Boss" through a "Guess the Title" game mode.

**Architecture:**
- **Backend:** Modular API views in `backend/api/animetix/api/games/world_boss.py`. Use Django signals for real-time phase updates via WebSockets.
- **Frontend:** Interactive UI using Framer Motion for boss status, and TanStack Query for data fetching.

**Tech Stack:**
- **Backend:** Django, Django Rest Framework, Channels (WebSockets).
- **Frontend:** React, Tailwind CSS, Framer Motion, Lucide React, TanStack Query.

---

### Task 1: Backend Serializers

**Files:**
- Modify: `backend/api/animetix/serializers.py`

- [ ] **Step 1: Add GlobalBoss and BossParticipation serializers**

- [ ] **Step 2: Commit**

---

### Task 2: World Boss API Views

**Files:**
- Create: `backend/api/animetix/api/games/world_boss.py`

- [ ] **Step 1: Implement World Boss logic**

- [ ] **Step 2: Commit**

---

### Task 3: API Registration

**Files:**
- Modify: `backend/api/animetix/api_views.py`
- Modify: `backend/api/animetix/urls/api.py`

- [ ] **Step 1: Export views in `api_views.py`**
- [ ] **Step 2: Add routes to `urls/api.py`**
- [ ] **Step 3: Commit**

---

### Task 4: Frontend UI - Boss Header & Status

**Files:**
- Modify: `frontend/src/features/games/WorldBossPage.tsx`

- [ ] **Step 1: Implement basic fetching and HP display**
- [ ] **Step 2: Commit**

---

### Task 5: Finalizing Attack Logic & UI

**Files:**
- Modify: `frontend/src/features/games/WorldBossPage.tsx`

- [ ] **Step 1: Add attack mutation and form**
- [ ] **Step 2: Commit**
