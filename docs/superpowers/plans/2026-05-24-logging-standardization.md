# Standardize Python Logging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all `print()` statements with a standardized `animetix` logger across the pipeline scripts in `backend/pipeline/anime/`, `backend/pipeline/characters/`, and `backend/pipeline/movies/`.

**Architecture:** Initialize `logger = logging.getLogger('animetix')` in each file and map `print()` calls to appropriate log levels (`info`, `warning`, `error`).

**Tech Stack:** Python standard `logging` library.

---

### Task 1: Standardize `backend/pipeline/anime/`

**Files:**
- Modify: `backend/pipeline/anime/6_generate_sagas.py`
- Modify: `backend/pipeline/anime/fetch_themes.py`
- Modify: `backend/pipeline/anime/filter_anime.py`
- Modify: `backend/pipeline/anime/ingest_anime.py`
- Modify: `backend/pipeline/anime/reconcile_drift.py`
- Modify: `backend/pipeline/anime/train_vibe_anime.py`
- Modify: `backend/pipeline/anime/vectorize_anime.py`

- [ ] **Step 1: Update `6_generate_sagas.py`**
  Add `import logging`, `logger = logging.getLogger('animetix')`, and replace `print` calls.
- [ ] **Step 2: Update `fetch_themes.py`**
  Add `import logging`, `logger = logging.getLogger('animetix')`, and replace `print` calls.
- [ ] **Step 3: Update `filter_anime.py`**
  Add `import logging`, `logger = logging.getLogger('animetix')`, and replace `print` calls.
- [ ] **Step 4: Update `ingest_anime.py`**
  Add `import logging`, `logger = logging.getLogger('animetix')`, and replace `print` calls.
- [ ] **Step 5: Update `reconcile_drift.py`**
  Add `import logging`, `logger = logging.getLogger('animetix')`, and replace `print` calls.
- [ ] **Step 6: Update `train_vibe_anime.py`**
  Add `import logging`, `logger = logging.getLogger('animetix')`, and replace `print` calls.
- [ ] **Step 7: Update `vectorize_anime.py`**
  Add `import logging`, `logger = logging.getLogger('animetix')`, and replace `print` calls.
- [ ] **Step 8: Verify no `print` remains in `backend/pipeline/anime/`**
  Run: `grep -r "print(" backend/pipeline/anime/`
- [ ] **Step 9: Commit**
  `git commit -m "refactor: standardize logging in backend/pipeline/anime/"`

### Task 2: Standardize `backend/pipeline/characters/`

**Files:**
- Modify: `backend/pipeline/characters/extract_akinetix_attributes.py`
- Modify: `backend/pipeline/characters/filter_characters.py`
- Modify: `backend/pipeline/characters/ingest_characters.py`
- Modify: `backend/pipeline/characters/ingest_vg_characters.py`
- Modify: `backend/pipeline/characters/refine_characters.py`
- Modify: `backend/pipeline/characters/train_vibe_characters.py`
- Modify: `backend/pipeline/characters/vectorize_characters.py`
- Modify: `backend/pipeline/characters/vectorize_vg_characters.py`

- [ ] **Step 1: Update `extract_akinetix_attributes.py`**
  Add `import logging`, `logger = logging.getLogger('animetix')`, and replace `print` calls.
- [ ] **Step 2: Update `filter_characters.py`**
  Add `import logging`, `logger = logging.getLogger('animetix')`, and replace `print` calls.
- [ ] **Step 3: Update `ingest_characters.py`**
  Add `import logging`, `logger = logging.getLogger('animetix')`, and replace `print` calls.
- [ ] **Step 4: Update `ingest_vg_characters.py`**
  Add `import logging`, `logger = logging.getLogger('animetix')`, and replace `print` calls.
- [ ] **Step 5: Update `refine_characters.py`**
  Add `import logging`, `logger = logging.getLogger('animetix')`, and replace `print` calls.
- [ ] **Step 6: Update `train_vibe_characters.py`**
  Add `import logging`, `logger = logging.getLogger('animetix')`, and replace `print` calls.
- [ ] **Step 7: Update `vectorize_characters.py`**
  Add `import logging`, `logger = logging.getLogger('animetix')`, and replace `print` calls.
- [ ] **Step 8: Update `vectorize_vg_characters.py`**
  Add `import logging`, `logger = logging.getLogger('animetix')`, and replace `print` calls.
- [ ] **Step 9: Verify no `print` remains in `backend/pipeline/characters/`**
  Run: `grep -r "print(" backend/pipeline/characters/`
- [ ] **Step 10: Commit**
  `git commit -m "refactor: standardize logging in backend/pipeline/characters/"`

### Task 3: Standardize `backend/pipeline/movies/`

**Files:**
- Modify: `backend/pipeline/movies/1_ingest_movies.py`
- Modify: `backend/pipeline/movies/3_filter_movies.py`
- Modify: `backend/pipeline/movies/5_vectorize_movies.py`
- Modify: `backend/pipeline/movies/6_cross_media_mapping.py`

- [ ] **Step 1: Update `1_ingest_movies.py`**
  Add `import logging`, `logger = logging.getLogger('animetix')`, and replace `print` calls.
- [ ] **Step 2: Update `3_filter_movies.py`**
  Add `import logging`, `logger = logging.getLogger('animetix')`, and replace `print` calls.
- [ ] **Step 3: Update `5_vectorize_movies.py`**
  Add `import logging`, `logger = logging.getLogger('animetix')`, and replace `print` calls.
- [ ] **Step 4: Update `6_cross_media_mapping.py`**
  Add `import logging`, `logger = logging.getLogger('animetix')`, and replace `print` calls.
- [ ] **Step 5: Verify no `print` remains in `backend/pipeline/movies/`**
  Run: `grep -r "print(" backend/pipeline/movies/`
- [ ] **Step 6: Commit**
  `git commit -m "refactor: standardize logging in backend/pipeline/movies/"`

### Task 4: Final Validation and Exception Handling Cleanup

- [ ] **Step 1: Final grep for `print(` in all target directories**
  Run: `grep -r "print(" backend/pipeline/{anime,characters,movies}/`
- [ ] **Step 2: Check for silent `except: pass` in modified files**
  Review the files modified for any `except: pass` and replace with `logger.exception` or `logger.warning`.
- [ ] **Step 3: Run one script from each category to verify logs are appearing**
  (e.g., `python backend/pipeline/anime/6_generate_sagas.py` - check output)
- [ ] **Step 4: Final commit**
  `git commit -m "docs: update spec and plan as completed"`
