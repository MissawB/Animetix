# Design Specification: Manga Extension Manager (Suwayomi) Verification & Testing

Verification and testing strategy for the Animetix Manga Extension Manager (Suwayomi integration), ensuring that downloading, updating, and deleting extensions works correctly and is robustly tested.

## 1. Objectives & Context

Animetix allows users to browse manga from external sources via a local Tachidesk/Suwayomi instance. The Extension Manager interface allows users to install, uninstall, and update these extensions (e.g. MangaDex, MangaFox, etc.) directly.
Although the backend endpoints and frontend components are already implemented, we need to:
- Establish proper JSDOM unit test naming in `vite.config.ts` to allow isolated unit test runs without storybook network conflicts.
- Mock `global.fetch` in the test runner setup to prevent relative URL fetching errors in secondary pages/components.
- Implement comprehensive frontend tests for `TachideskExplorerPage` to cover listing, filtering, search, and action requests for extensions.
- Mark the task complete in tracking files.

## 2. Proposed Changes

### 2.1 Test Infrastructure

#### `frontend/vite.config.ts`
- Add `name: 'unit'` to the JSDOM unit test project configuration. This enables isolated testing via `vitest run --project=unit`.

#### `frontend/src/test/setup.ts`
- Implement a global `fetch` mock that prevents relative URL requests (`/api/...`) from failing with `ERR_INVALID_URL` in Node.js.

### 2.2 New Frontend Tests

#### `frontend/src/pages/explore/__tests__/TachideskExplorerPage.test.tsx`
Write a test suite covering the following scenarios:
1. **Initial Render**: The page displays the header title "Tachidesk Explorer" and defaults to the "Catalogue" tab.
2. **Tab Switch**: Clicking the "Extensions" tab successfully fetches the extensions list from the `/api/v1/explore/suwayomi/extensions/` endpoint and updates the UI state.
3. **Extension Listing**: Extensions are correctly grouped into categories:
   - "Mises à jour disponibles" (extensions with `hasUpdate = true`).
   - "Extensions Installées" (installed extensions with `isInstalled = true` and `hasUpdate = false`).
   - "Extensions Disponibles" (not installed with `isInstalled = false`).
4. **Search and Filtering**: Typing in the search input filters extensions by name, package name, or language.
5. **Action Handlers**:
   - Clicking **Install** calls `/api/v1/explore/suwayomi/extensions/action/` with `action: 'install'` and the correct package name.
   - Clicking **Uninstall** calls `/api/v1/explore/suwayomi/extensions/action/` with `action: 'uninstall'`.
   - Clicking **Update** calls `/api/v1/explore/suwayomi/extensions/action/` with `action: 'update'`.
   - Action triggers local button loading states and subsequent data refetch.
6. **Error States**: Display error messages properly if the API returns a failure status.

## 3. Verification Plan

### Automated Tests
- Run `npm run test -- --project=unit` in the `frontend` folder to run all JSDOM-based unit tests.
- Run `.venv/Scripts/pytest` for backend verification.
- Run `npm run check-types` in `frontend` for type check.

### Manual Verification
- Verify the TODO marks are updated.
