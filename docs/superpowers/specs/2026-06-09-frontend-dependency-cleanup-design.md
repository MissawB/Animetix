# Design Spec: Frontend Dependency Cleanup (2026-06-09)

## 1. Context & Problem Statement
The Animetix frontend currently lists `three` and `plotly.js` as top-level dependencies in `package.json`. However, these are also required as peer dependencies by `@google/model-viewer` and `react-plotly.js`, respectively. 
Listing them at the top level is redundant and can cause version conflicts or bloated lockfiles.

## 2. Goals
- Streamline `package.json` by removing redundant top-level dependencies.
- Ensure the dependency tree remains valid and functional via peer dependency resolution.
- Verify that removal doesn't break type definitions or component functionality.

## 3. Technical Approach

### 3.1 Dependency Removal
We will remove the following packages from the `dependencies` section of `frontend/package.json`:
- `three`: Provided by `@google/model-viewer`.
- `plotly.js`: Provided by `react-plotly.js`.

### 3.2 Lockfile Synchronization
After updating `package.json`, we will run `npm install` (or `npm prune`) to ensure `package-lock.json` reflects the optimized tree. Modern npm (v7+) automatically installs peer dependencies, so this should maintain the required packages in `node_modules`.

### 3.3 Verification
- **Build Integrity**: Ensure components using these libraries (`SpatialLabPage.tsx`, `ArchetypeNexusPage.tsx`, `LatentSpacePage.tsx`) still compile and function.
- **Types**: Verify that `npm run check-types` passes. We have a manual declaration in `src/types/plotly.d.ts` that provides basic type safety for Plotly imports.
- **Linter**: Ensure `npm run lint` remains clean of parsing or import errors.

## 4. Components Involved
- `frontend/package.json`
- `frontend/package-lock.json`

## 5. Success Criteria
- `package.json` no longer contains `three` or `plotly.js`.
- `npm run check-types` and `npm run lint` pass without new errors.
- `node_modules` still contains `three` and `plotly.js` as sub-dependencies of their respective wrappers.
