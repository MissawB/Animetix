# Frontend Accessibility Cleanup Implementation Plan (v2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve keyboard navigation and screen reader issues identified by `jsx-a11y` in the frontend.

**Architecture:** 
- Standardize label-input associations using `htmlFor` and `id`.
- Enhance interactive elements with semantic roles, tab indexing, and keyboard listeners.
- Add caption tracks to media elements.

**Tech Stack:** React, TypeScript, Tailwind CSS, Lucide React, Framer Motion.

---

### Task 1: Form Label Associations (Comprehensive)

**Files:**
- Modify: `frontend/src/pages/auth/LoginPage.tsx`
- Modify: `frontend/src/pages/auth/RegisterPage.tsx`
- Modify: `frontend/src/pages/social/ClubDiscoveryPage.tsx`
- Modify: `frontend/src/pages/social/AIDebateArenaPage.tsx`
- Modify: `frontend/src/pages/social/AIFeedbackHistoryPage.tsx`
- Modify: `frontend/src/pages/social/ClubDashboard.tsx`
- Modify: `frontend/src/pages/support/SupportDashboardPage.tsx`

- [ ] **Step 1: Fix Auth pages labels**
Add `id` to inputs and matching `htmlFor` to labels in `LoginPage.tsx` and `RegisterPage.tsx`.

- [ ] **Step 2: Fix Social pages labels**
Fix label associations in `ClubDiscoveryPage.tsx`, `AIDebateArenaPage.tsx`, `AIFeedbackHistoryPage.tsx`, and `ClubDashboard.tsx`.

- [ ] **Step 3: Fix Support page labels**
Fix label associations in `SupportDashboardPage.tsx`.

- [ ] **Step 4: Verify with lint**
Run: `npx eslint src/pages/auth/*.tsx src/pages/social/*.tsx src/pages/support/*.tsx`
Expected: `jsx-a11y/label-has-associated-control` errors should be gone for these files.

- [ ] **Step 5: Commit**
```bash
git add frontend/src/pages/auth/ frontend/src/pages/social/ frontend/src/pages/support/
git commit -m "fix(a11y): associate labels with form controls across auth, social, and support pages"
```

---

### Task 2: UI Component Keyboard Accessibility

**Files:**
- Modify: `frontend/src/components/Navbar.tsx`
- Modify: `frontend/src/components/Layout.tsx`
- Modify: `frontend/src/components/ui/Card.tsx`

- [ ] **Step 1: Refactor Navbar**
Add keyboard support and ARIA roles to interactive elements in `Navbar.tsx`.

- [ ] **Step 2: Refactor Layout**
Fix click events on non-interactive elements in `Layout.tsx` (e.g., sidebar toggles or overlays).

- [ ] **Step 3: Refactor Card component**
Add `onKeyDown` and appropriate roles if the `Card` component is clickable.

- [ ] **Step 4: Verify with lint**
Run: `npx eslint src/components/Navbar.tsx src/components/Layout.tsx src/components/ui/Card.tsx`
Expected: `jsx-a11y/click-events-have-key-events` and `jsx-a11y/no-static-element-interactions` errors should be gone.

- [ ] **Step 5: Commit**
```bash
git add frontend/src/components/Navbar.tsx frontend/src/components/Layout.tsx frontend/src/components/ui/Card.tsx
git commit -m "fix(a11y): add keyboard support and ARIA roles to core UI components"
```

---

### Task 3: Media & Captions

**Files:**
- Modify: `frontend/src/pages/labs/MangaVoicePage.tsx`

- [ ] **Step 1: Add track element to audio**
Add `<track kind="captions" />` to the `<audio>` element.

- [ ] **Step 2: Verify with lint**
Run: `npx eslint src/pages/labs/MangaVoicePage.tsx`
Expected: `jsx-a11y/media-has-caption` error should be gone.

- [ ] **Step 3: Commit**
```bash
git add frontend/src/pages/labs/MangaVoicePage.tsx
git commit -m "fix(a11y): add caption track to audio element in MangaVoicePage"
```

---

### Task 4: Final Validation

- [ ] **Step 1: Run project-wide lint**
Run: `npm run lint`
Expected: 0 `jsx-a11y/*` errors.

- [ ] **Step 2: Final Commit**
```bash
git commit --allow-empty -m "chore: frontend accessibility cleanup complete"
```
