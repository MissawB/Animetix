# Offline Sync Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct the Offline Sync API URL path in the frontend and disable ratelimiting in Django test settings to ensure the test suite and integration work correctly.

**Architecture:** Update the api request URL in the React frontend and disable django-ratelimit in `test_settings.py` for testing isolation.

**Tech Stack:** React, TypeScript, Django, Pytest, django-ratelimit

---

### Task 1: Disable Ratelimiting in Backend Test Settings

**Files:**
- Modify: [test_settings.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/api/animetix_project/test_settings.py)

- [ ] **Step 1: Add RATELIMIT_ENABLE setting**

Add the setting `RATELIMIT_ENABLE = False` at the end of the file.

```python
RATELIMIT_ENABLE = False
```

- [ ] **Step 2: Run pytest to verify all tests in test_sync.py pass**

Run: `.venv\Scripts\pytest tests/api/test_sync.py`
Expected output: `6 passed`

- [ ] **Step 3: Commit backend test settings change**

```bash
git add backend/api/animetix_project/test_settings.py
git commit -m "test: disable django ratelimiting in test settings to pass sync tests"
```

---

### Task 2: Correct API URL in Frontend Sync Page

**Files:**
- Modify: [OfflineSyncPage.tsx](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/frontend/src/pages/social/OfflineSyncPage.tsx)

- [ ] **Step 1: Update API URL**

Change `/api/sync/offline/` to `/api/v1/sync/offline/` at line 97 of `OfflineSyncPage.tsx`.

```typescript
      const response = await apiClient('/api/v1/sync/offline/', {
        method: 'POST',
        body: JSON.stringify(offlineGames),
      });
```

- [ ] **Step 2: Run frontend TypeScript compilation check**

Navigate to frontend directory (or run in `frontend/`) and run `npm run build` or `npx tsc --noEmit` to verify no type or import errors.

- [ ] **Step 3: Commit frontend page change**

```bash
git add frontend/src/pages/social/OfflineSyncPage.tsx
git commit -m "fix: correct api endpoint route to /api/v1/sync/offline/ in OfflineSyncPage"
```
