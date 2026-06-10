# Design Spec: Frontend Accessibility (A11Y) Cleanup (2026-06-09)

## 1. Context & Problem Statement
An initial audit using `eslint-plugin-jsx-a11y` revealed several accessibility barriers in the Animetix frontend:
- **Missing Label Associations**: Inputs in forms (Login, Register, Club Discovery) lack explicit links to their labels.
- **Static Click Handlers**: The `Navbar` and other UI elements use `onClick` on non-interactive elements without keyboard support.
- **Media Inaccessibility**: Audio elements lack caption tracks.
- **Keyboard Navigation**: Incomplete focus management in custom interactive components.

## 2. Goals
- Ensure 100% compliance with `jsx-a11y/recommended` rules.
- Enable full keyboard navigation for core features (Auth, Navbar, Social).
- Improve screen reader experience by providing appropriate roles and labels.

## 3. Technical Approach

### 3.1 Form Accessibility
- **Strategy**: Use `htmlFor` on `<label>` and matching `id` on inputs.
- **Target Files**: 
    - `src/pages/auth/LoginPage.tsx`
    - `src/pages/auth/RegisterPage.tsx`
    - `src/pages/social/ClubDiscoveryPage.tsx`

### 3.2 Interactive Elements & Navbar
- **Strategy**:
    - Convert `div` click handlers to `button` elements or add `role="button"` + `tabIndex={0}`.
    - Add `onKeyDown` handlers for keyboard interaction.
- **Target Files**:
    - `src/components/Navbar.tsx`
    - `src/components/ui/Card.tsx` (if applicable)

### 3.3 Media
- **Strategy**: Add empty caption tracks or appropriate attributes to audio/video elements.
- **Target Files**:
    - `src/pages/labs/MangaVoicePage.tsx`

### 3.4 Verification
- **Automated**: `npm run lint` must show 0 `jsx-a11y` errors.
- **Manual**: Verify that all interactive elements are reachable and activatable via `Tab` + `Enter/Space`.

## 4. Components Involved
- `frontend/src/components/Navbar.tsx`
- `frontend/src/pages/auth/LoginPage.tsx`
- `frontend/src/pages/auth/RegisterPage.tsx`
- `frontend/src/pages/social/ClubDiscoveryPage.tsx`
- `frontend/src/pages/labs/MangaVoicePage.tsx`

## 5. Success Criteria
- Zero accessibility errors in the lint output.
- Navigation through the main menu using only the keyboard is functional.
- Form fields are clearly identified for screen readers.
