# Specification: Frontend i18n Externalization (Remaining Waves)

## 1. Goal
Externalize the remaining hardcoded French UI strings (~150 files across `labs`, `social`, `admin`, `media`, `search`, and `dev`) into `translation.json` for English (`en`) and French (`fr`). Align the codebase with the established house pattern:
```typescript
t('key.path', 'Exact French text default')
```
This ensures that if translations are missing at runtime or in tests, the system seamlessly falls back to the exact French text.

## 2. Proposed Wave Partitioning
To manage the change size safely, the work is split into three waves:

* **Wave 1: Labs**
  * Target Directories: `frontend/src/pages/labs/`, `frontend/src/features/labs/`
  * Total files: ~35
* **Wave 2: Social, Search, & Media**
  * Target Directories: `frontend/src/pages/social/`, `frontend/src/pages/search/`, `frontend/src/pages/media/`, `frontend/src/features/social/`, `frontend/src/features/search/`, `frontend/src/features/media/`
  * Total files: ~30
* **Wave 3: Admin & Dev**
  * Target Directories: `frontend/src/pages/admin/`, `frontend/src/pages/dev/`, `frontend/src/features/admin/`, `frontend/src/components/admin/`
  * Total files: ~25

## 3. Key Naming Scheme
We will structure the translation keys hierarchically:
* **Labs:** `labs.<page/feature>.<element>` (e.g., `labs.audio.recording_active`)
* **Social:** `social.<page/feature>.<element>` (e.g., `social.profile.sync_status`)
* **Media:** `media.<page/feature>.<element>` (e.g., `media.library.no_downloads`)
* **Search:** `search.<page/feature>.<element>` (e.g., `search.expert.waiting_query`)
* **Admin:** `admin.<page/feature>.<element>` (e.g., `admin.health.uptime`)
* **Dev:** `dev.<page/feature>.<element>` (e.g., `dev.portal.generate_key`)

*Note: Brand names ("Animetix", "Berrix", etc.) and code-only strings like enum keys/API payload string literals remain as-is.*

## 4. Fragment Merge Logic
To prevent large file churn and merge conflicts in `translation.json`, the translation keys will be compiled into temporary JSON fragment files during replacement:
* **Paths:**
  * French: `frontend/src/i18n/fragments/fr/<batch_name>.json`
  * English: `frontend/src/i18n/fragments/en/<batch_name>.json`

A dedicated script, `scripts/curation/merge_translation_fragments.py`, will be run after each batch/wave to:
1. Parse the fragments recursively.
2. Load and merge keys into the main translation files.
3. Sort all keys alphabetically at each level of nesting.
4. Save the main files with 2-space indentation.
5. Safely delete the merged fragment files.

## 5. Verification Plan
After each wave's replacement and merge:
* **Consistency Check:** Run `python scripts/curation/compare_translations.py` to ensure that EN and FR files have 100% matching key structures.
* **Test Verification:** Run Vitest unit tests to ensure mock translations resolve correctly.
* **Compilation Check:** Run `npm run tsc` or Vite build checks to ensure no TypeScript compilation or parsing issues were introduced.
