# Design Spec: Frontend Build Stabilization (2026-06-09)

## 1. Context & Problem Statement
The Animetix frontend build is currently unstable. 
- **ESLint**: 305 parsing errors occur because `eslint.config.js` does not handle TypeScript/TSX syntax.
- **TypeScript**: 8 compilation errors exist in `MangaVoicePage.tsx` and `ArchetypeNexusPage.tsx` due to malformed JSX tags and misplaced braces.
- **False Positives**: Missing component errors (e.g., `AnimatedPage`) are likely resulting from these primary parsing failures.

## 2. Goals
- Eliminate all ESLint parsing errors.
- Resolve all TypeScript compilation errors.
- Standardize build verification scripts.

## 3. Technical Approach

### 3.1 ESLint Configuration Update
We will migrate to `typescript-eslint` to support modern Flat Config for TypeScript.
- **Actions**:
    - Install `typescript-eslint` as a dev dependency.
    - Update `eslint.config.js` to include the TypeScript parser and recommended rules.
    - Ensure `globals.browser` and `globals.node` (for config files) are correctly scoped.

### 3.2 Syntax Fixes
#### `MangaVoicePage.tsx`
- Fix the closing tag of the "SAUVEGARDER" button which currently uses `</p>` instead of `</Button>`.

#### `ArchetypeNexusPage.tsx`
- Fix the mismatched tags. The current structure has a `div` wrapping `AnimatedPage`, but the closing order or presence is incorrect.
- Correct the `StatBar` component definition which has a syntax error in its interface/declaration block.

### 3.3 Verification
- Use `npm run check-types` (`tsc --noEmit`) to verify structural integrity.
- Use `npm run lint` (`eslint .`) to verify stylistic and parsing correctness.

## 4. Components Involved
- `frontend/package.json`
- `frontend/eslint.config.js`
- `frontend/src/pages/labs/MangaVoicePage.tsx`
- `frontend/src/pages/social/ArchetypeNexusPage.tsx`

## 5. Success Criteria
- `npm run lint` passes without errors.
- `npm run check-types` passes without errors.
