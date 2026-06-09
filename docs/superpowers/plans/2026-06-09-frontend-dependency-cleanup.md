# Frontend Dependency Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove redundant top-level dependencies (`three`, `plotly.js`) from the frontend.

**Architecture:** 
- Leverage npm peer dependency auto-installation.
- Maintain manual type definitions where necessary.

**Tech Stack:** npm, React, TypeScript.

---

### Task 1: Dependency Removal & Lockfile Sync

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: Remove redundant dependencies from package.json**

Run: `npm uninstall three plotly.js` (in `frontend` directory)
Expected: `three` and `plotly.js` removed from `dependencies`. `package-lock.json` updated.

- [ ] **Step 2: Verify dependency presence**

Run: `ls node_modules/three` and `ls node_modules/plotly.js` (in `frontend` directory)
Expected: Both directories should still exist as they are required by `@google/model-viewer` and `react-plotly.js`.

- [ ] **Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "build: remove redundant three and plotly.js dependencies"
```

---

### Task 2: Verification

- [ ] **Step 1: Run type check**

Run: `npm run check-types`
Expected: `Found 0 errors`.

- [ ] **Step 2: Run linter**

Run: `npm run lint`
Expected: No new lint errors related to missing modules.

- [ ] **Step 3: Final verification of components**

Run: `npm run build`
Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
git commit --allow-empty -m "chore: dependency cleanup complete"
```
