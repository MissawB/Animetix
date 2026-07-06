# Frontend i18n Externalization (Remaining Waves) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Externalize all remaining hardcoded French strings (~150 files) across labs, social, admin, media, search, and dev into English and French translation JSON files, using a hybrid approach of batch code editing, fragment generation, and script-based merging.

**Architecture:** We will process files in batches by category. For each batch, we replace French strings in React/TSX files with `t('key.path', 'Exact French text default')` and generate JSON fragments in `frontend/src/i18n/fragments/{en|fr}/`. A Python script will then merge these fragments into the main translation files, sorting keys alphabetically.

**Tech Stack:** React, TypeScript, i18next, react-i18next, Python, Vitest.

---

### Task 1: Create the Fragment Merge Script

**Files:**
- Create: `scripts/curation/merge_translation_fragments.py`

- [ ] **Step 1: Write the merge script**
  Create the file `scripts/curation/merge_translation_fragments.py` with the following content:
  ```python
  import os
  import json
  import glob

  def merge_dicts(dict1, dict2):
      for k, v in dict2.items():
          if k in dict1:
              if isinstance(dict1[k], dict) and isinstance(v, dict):
                  merge_dicts(dict1[k], v)
              elif dict1[k] != v:
                  print(f"⚠️ Warning: Conflict on key '{k}' ('{dict1[k]}' vs '{v}'). Keeping existing value.")
          else:
              dict1[k] = v

  def sort_dict(d):
      return {k: sort_dict(v) if isinstance(v, dict) else v for k, v in sorted(d.items())}

  def main():
      root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
      fragments_dir = os.path.join(root_dir, "frontend", "src", "i18n", "fragments")
      locales_dir = os.path.join(root_dir, "frontend", "public", "locales")
      
      for lng in ["en", "fr"]:
          main_file = os.path.join(locales_dir, lng, "translation.json")
          if not os.path.exists(main_file):
              print(f"❌ Main file not found: {main_file}")
              continue
              
          with open(main_file, "r", encoding="utf-8") as f:
              try:
                  main_data = json.load(f)
              except Exception as e:
                  print(f"❌ Failed to parse {main_file}: {e}")
                  continue
              
          frag_pattern = os.path.join(fragments_dir, lng, "*.json")
          fragments = glob.glob(frag_pattern)
          
          if not fragments:
              print(f"ℹ️ No fragments found for language: {lng}")
              continue
              
          for frag_path in fragments:
              print(f"⚙️ Merging fragment: {frag_path}")
              with open(frag_path, "r", encoding="utf-8") as f:
                  try:
                      frag_data = json.load(f)
                  except Exception as e:
                      print(f"❌ Failed to parse {frag_path}: {e}")
                      continue
              merge_dicts(main_data, frag_data)
              
          # Sort and write back
          sorted_data = sort_dict(main_data)
          with open(main_file, "w", encoding="utf-8") as f:
              json.dump(sorted_data, f, ensure_ascii=False, indent=2)
          print(f"✅ Main translation file updated: {main_file}")
          
          # Delete fragments
          for frag_path in fragments:
              try:
                  os.remove(frag_path)
                  print(f"🗑️ Deleted fragment: {frag_path}")
              except Exception as e:
                  print(f"❌ Failed to delete fragment {frag_path}: {e}")

  if __name__ == "__main__":
      main()
  ```

- [ ] **Step 2: Run a validation check for the merge script**
  Create dummy fragment files in `frontend/src/i18n/fragments/fr/dummy.json` and `frontend/src/i18n/fragments/en/dummy.json`.
  Run: `python scripts/curation/merge_translation_fragments.py`
  Verify that the main files are sorted alphabetically and dummy keys are added, and that dummy files are deleted.

- [ ] **Step 3: Commit**
  Run:
  ```bash
  git add scripts/curation/merge_translation_fragments.py
  git commit -m "feat(i18n): add translation fragment merge script"
  ```

---

### Task 2: Wave 1 — Labs (Batch A)

**Files:**
- Modify: Files under `frontend/src/pages/labs/` (AudioLabPage, CinematicReconstructionPage, CognitionHubPage, CompilerLabPage, CoveOraclePage, DioramaGalleryPage, ForgeHubPage, LabHubPage, LatentSpacePage, LiquidNeuralNetworkLabPage)
- Create: `frontend/src/i18n/fragments/fr/wave1_labs_a.json`
- Create: `frontend/src/i18n/fragments/en/wave1_labs_a.json`

- [ ] **Step 1: Replace French strings in code**
  Modify target TSX files in Wave 1 Batch A. Replace raw French strings with `t('labs.<page>.<key>', 'default FR')`.
  Ensure `import { useTranslation } from 'react-i18next';` and `const { t } = useTranslation();` are present in each component.
  
- [ ] **Step 2: Write translation fragments**
  Create `wave1_labs_a.json` in both French and English under `frontend/src/i18n/fragments/fr/` and `frontend/src/i18n/fragments/en/`. E.g., for French:
  ```json
  {
    "labs": {
      "audio": {
        "text_validation": "Veuillez entrer au moins 10 caractères pour la synthèse.",
        "text_too_long": "Le texte est trop long."
      }
    }
  }
  ```
  And the corresponding English translations in `en/wave1_labs_a.json`.

- [ ] **Step 3: Merge fragments**
  Run: `python scripts/curation/merge_translation_fragments.py`

- [ ] **Step 4: Run consistency checks**
  Run: `python scripts/curation/compare_translations.py`
  Verify that the build is correct: `npm run tsc` (or test with Vitest: `npm run test` or `npx vitest run`).

- [ ] **Step 5: Commit**
  Run:
  ```bash
  git add frontend/src/pages/labs/ frontend/public/locales/
  git commit -m "feat(i18n): externalize Wave 1 Labs Batch A strings"
  ```

---

### Task 3: Wave 1 — Labs (Batch B)

**Files:**
- Modify: Remaining pages under `frontend/src/pages/labs/` (MangaLabPage, MangaVoicePage, MultiverseCatalogPage, MultiverseStudioPage, NeuralDiagnosticsPage, QuantumLabPage, SeiyuuDiscoveryPage, SingularityCommandCenterPage, SoundscapeLabPage, SpatialLabPage, SpeechToSpeechLabPage, StrategyLabPage, SwarmLabPage, SynapticLabPage, TreeOfThoughtsPage, VideoLabPage, VideoRagPage, VisualNexusPage, VoiceLabPage) and related components under `frontend/src/pages/labs/multiverse-catalog/components/` and hooks.
- Create: `frontend/src/i18n/fragments/fr/wave1_labs_b.json`
- Create: `frontend/src/i18n/fragments/en/wave1_labs_b.json`

- [ ] **Step 1: Replace French strings in code**
  Add the `useTranslation` hook and wrap all remaining French strings with `t(...)` in all Wave 1 Batch B files.

- [ ] **Step 2: Write translation fragments**
  Create `wave1_labs_b.json` in both French and English fragment folders.

- [ ] **Step 3: Merge fragments**
  Run: `python scripts/curation/merge_translation_fragments.py`

- [ ] **Step 4: Run consistency checks and tests**
  Run: `python scripts/curation/compare_translations.py` and verify with Vitest unit tests.

- [ ] **Step 5: Commit**
  Run:
  ```bash
  git add frontend/src/pages/labs/ frontend/public/locales/
  git commit -m "feat(i18n): externalize Wave 1 Labs Batch B strings"
  ```

---

### Task 4: Wave 2 — Social, Search, & Media (Batch A)

**Files:**
- Modify: Target pages under `frontend/src/pages/social/` (AchievementsPage, AIDebateArenaPage, AIFeedbackHistoryPage, ArchetypeNexusPage, ClubDashboard, ClubDiscoveryPage, ClubEventPage, CollectionPage, CommunityFeedPage, FriendsPage)
- Create: `frontend/src/i18n/fragments/fr/wave2_a.json`
- Create: `frontend/src/i18n/fragments/en/wave2_a.json`

- [ ] **Step 1: Replace French strings in code**
  Implement `t('social.<page>.<key>', 'default FR')` wraps for hardcoded French strings.

- [ ] **Step 2: Write translation fragments**
  Create `wave2_a.json` in both French and English fragment folders.

- [ ] **Step 3: Merge fragments**
  Run: `python scripts/curation/merge_translation_fragments.py`

- [ ] **Step 4: Run consistency checks and tests**
  Run: `python scripts/curation/compare_translations.py` and verify with Vitest unit tests.

- [ ] **Step 5: Commit**
  Run:
  ```bash
  git add frontend/src/pages/social/ frontend/public/locales/
  git commit -m "feat(i18n): externalize Wave 2 Social Batch A strings"
  ```

---

### Task 5: Wave 2 — Social, Search, & Media (Batch B)

**Files:**
- Modify: Remaining pages under `frontend/src/pages/social/` (LeaderboardPage, NeuroMemoryPage, NotificationsPage, OfflineSyncPage, OpenDataPage, ProfilePage, SocialDashboard, SocialHubPage, TransparencyPage), pages under `frontend/src/pages/search/` (CounterfactualSimulatorPage, ExpertNexusPage, UniversalSearchHubPage), and pages under `frontend/src/pages/media/` (CharacterDetailPage, MangaLibraryPage, MangaReaderPage, MediaDetailPage, OfflineMangaPage, StaffDetailPage) and hooks.
- Create: `frontend/src/i18n/fragments/fr/wave2_b.json`
- Create: `frontend/src/i18n/fragments/en/wave2_b.json`

- [ ] **Step 1: Replace French strings in code**
  Wrap remaining French strings with `t(...)` in all Wave 2 Batch B files.

- [ ] **Step 2: Write translation fragments**
  Create `wave2_b.json` in both French and English fragment folders.

- [ ] **Step 3: Merge fragments**
  Run: `python scripts/curation/merge_translation_fragments.py`

- [ ] **Step 4: Run consistency and tests**
  Run: `python scripts/curation/compare_translations.py` and verify with Vitest unit tests.

- [ ] **Step 5: Commit**
  Run:
  ```bash
  git add frontend/src/pages/social/ frontend/src/pages/search/ frontend/src/pages/media/ frontend/public/locales/
  git commit -m "feat(i18n): externalize Wave 2 Batch B strings"
  ```

---

### Task 6: Wave 3 — Admin & Dev

**Files:**
- Modify: Pages under `frontend/src/pages/admin/` (AdminCurationPage, AdminDashboardPage, AdminDSPyDashboard, AdminEvalPage, AdminGoldDatasetPage, AISafetyAuditPage, ClusterHealthPanel, EconomicAuditPage, FinancialDashboardPage, GraphDebuggerPage, HealthPage, MLOpsDashboard, SOTABenchmarkPage, TTCMonitoringPage, UserManagementPage), pages under `frontend/src/pages/dev/` (ApiHubPage, DeveloperPortalPage, MLOpsConsolePage, ObservabilityConsolePage), features/components under `admin/`.
- Create: `frontend/src/i18n/fragments/fr/wave3.json`
- Create: `frontend/src/i18n/fragments/en/wave3.json`

- [ ] **Step 1: Replace French strings in code**
  Implement `t('admin.<page>.<key>', 'default FR')` and `t('dev.<page>.<key>', 'default FR')` wraps for hardcoded French strings.

- [ ] **Step 2: Write translation fragments**
  Create `wave3.json` in both French and English fragment folders.

- [ ] **Step 3: Merge fragments**
  Run: `python scripts/curation/merge_translation_fragments.py`

- [ ] **Step 4: Run consistency and tests**
  Run: `python scripts/curation/compare_translations.py` and verify with Vitest unit tests.

- [ ] **Step 5: Commit**
  Run:
  ```bash
  git add frontend/src/pages/admin/ frontend/src/pages/dev/ frontend/public/locales/
  git commit -m "feat(i18n): externalize Wave 3 Admin & Dev strings"
  ```

---

### Task 7: Fix Pre-existing i18n Mismatches and Verify

**Files:**
- Modify: `frontend/public/locales/en/translation.json`, `frontend/public/locales/fr/translation.json`

- [ ] **Step 1: Fix pre-existing key mismatch**
  Ensure the keys mismatch reported by `compare_translations.py` (`games.akinetix.*` vs `labs.akinetix.*`) are reconciled. Adjust them to the correct location or double-add them so both match.
  
- [ ] **Step 2: Run a final full check**
  Run: `python scripts/curation/compare_translations.py`
  Expected: "All keys are consistent between EN and FR." (Exit code 0)
  
- [ ] **Step 3: Run Vitest unit tests**
  Run: `npx vitest run` or check standard unit test commands.
  Expected: All tests pass.
  
- [ ] **Step 4: Run TypeScript build compilation check**
  Run: `npm run tsc` or `npx tsc --noEmit` from `frontend/` to make sure there are no TypeScript compilation errors.
  
- [ ] **Step 5: Commit**
  Run:
  ```bash
  git add frontend/public/locales/
  git commit -m "fix(i18n): reconcile pre-existing mismatches and finalize all waves"
  ```
