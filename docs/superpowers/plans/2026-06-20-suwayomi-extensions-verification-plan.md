# Manga Extension Manager (Suwayomi) Verification & Testing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure the manga extension manager (install, uninstall, update) is fully integrated and robustly tested without breaking test suite or storybook runners.

**Architecture:** Add a name `'unit'` to the JSDOM test configuration project in `vite.config.ts`. Mock `global.fetch` globally to handle relative endpoint requests. Implement a complete set of Vitest unit tests in `TachideskExplorerPage.test.tsx` verifying extension listing, filtering, search, and action dispatching.

**Tech Stack:** React 19, TypeScript, Vitest, Testing Library, MSW/Fetch Mocking.

---

### Task 1: JSDOM Project Configuration

**Files:**
- Modify: `frontend/vite.config.ts`

- [ ] **Step 1: Edit configuration to name the JSDOM project**
      Add `name: 'unit'` to the first configuration object under `test.projects`.

- [ ] **Step 2: Verify unit tests project runs**
      Run: `npx vitest run --project=unit`
      Expected: Runs only unit tests and passes.

- [ ] **Step 3: Commit configuration changes**
      Run: `git add frontend/vite.config.ts && git commit -m "test: configure unit test project in vite.config.ts"`

---

### Task 2: Fallback Global Fetch Mock

**Files:**
- Modify: `frontend/src/test/setup.ts`

- [ ] **Step 1: Add a global fetch mock fallback to setup.ts**
      Check if `global.fetch` is already defined and, if so, mock it to avoid relative URL errors.

- [ ] **Step 2: Verify existing tests run successfully**
      Run: `npx vitest run --project=unit`
      Expected: Tests pass with no ERR_INVALID_URL errors.

- [ ] **Step 3: Commit setup changes**
      Run: `git add frontend/src/test/setup.ts && git commit -m "test: add global fetch mock fallback in setup.ts"`

---

### Task 3: Create TachideskExplorerPage Unit Tests

**Files:**
- Create: `frontend/src/pages/explore/__tests__/TachideskExplorerPage.test.tsx`

- [ ] **Step 1: Write unit tests for TachideskExplorerPage**
      Write tests mock-fetching extensions and validating UI components, tabs, search, and action clicks.

- [ ] **Step 2: Run new unit tests**
      Run: `npx vitest run --project=unit src/pages/explore/__tests__/TachideskExplorerPage.test.tsx`
      Expected: All test cases pass.

- [ ] **Step 3: Commit new test suite**
      Run: `git add frontend/src/pages/explore/__tests__/TachideskExplorerPage.test.tsx && git commit -m "test: add unit tests for TachideskExplorerPage"`

---

### Task 4: Mark Manga Extension Manager Complete

**Files:**
- Modify: `TODO.md`
- Modify: `docs/TODO.md`

- [ ] **Step 1: Check off the Manga Extension Manager item**
      Update the markdown files to check `[x]` for **Manga Extension Manager (Suwayomi)**.

- [ ] **Step 2: Commit documentation changes**
      Run: `git add TODO.md docs/TODO.md && git commit -m "docs: mark manga extension manager task as complete"`
