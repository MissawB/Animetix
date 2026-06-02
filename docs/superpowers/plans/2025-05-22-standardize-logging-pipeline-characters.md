# Standardize Python Logging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Standardize logging in `backend/pipeline/characters/*.py` by replacing `print()` calls with `logger` methods.

**Architecture:** Inject `import logging` and `logger = logging.getLogger("animetix." + __name__)` at the top level of each file. Use `logger.info`, `logger.error`, or `logger.warning` based on the context (emojis often indicate the level: ❌ for error, ⚠️ for warning, etc.).

**Tech Stack:** Python, `logging` library.

---

### Task 1: Update `backend/pipeline/characters/extract_akinetix_attributes.py`

**Files:**
- Modify: `backend/pipeline/characters/extract_akinetix_attributes.py`

- [ ] **Step 1: Inject Logger**
Add `import logging` and `logger = logging.getLogger("animetix." + __name__)` at the top.

- [ ] **Step 2: Replace prints**
Replace all `print()` with `logger.info`, `logger.error`, or `logger.warning`.

- [ ] **Step 3: Verify syntax**
Run: `python -m py_compile backend/pipeline/characters/extract_akinetix_attributes.py`

### Task 2: Update `backend/pipeline/characters/filter_characters.py`

**Files:**
- Modify: `backend/pipeline/characters/filter_characters.py`

- [ ] **Step 1: Inject Logger**
- [ ] **Step 2: Replace prints**
- [ ] **Step 3: Verify syntax**

### Task 3: Update `backend/pipeline/characters/ingest_characters.py`

**Files:**
- Modify: `backend/pipeline/characters/ingest_characters.py`

- [ ] **Step 1: Inject Logger**
- [ ] **Step 2: Replace prints**
- [ ] **Step 3: Verify syntax**

### Task 4: Update `backend/pipeline/characters/ingest_vg_characters.py`

**Files:**
- Modify: `backend/pipeline/characters/ingest_vg_characters.py`

- [ ] **Step 1: Inject Logger**
- [ ] **Step 2: Replace prints**
- [ ] **Step 3: Verify syntax**

### Task 5: Update `backend/pipeline/characters/refine_characters.py`

**Files:**
- Modify: `backend/pipeline/characters/refine_characters.py`

- [ ] **Step 1: Inject Logger**
- [ ] **Step 2: Replace prints**
- [ ] **Step 3: Verify syntax**

### Task 6: Update `backend/pipeline/characters/train_vibe_characters.py`

**Files:**
- Modify: `backend/pipeline/characters/train_vibe_characters.py`

- [ ] **Step 1: Inject Logger** (already has `import logging`, just add `logger`)
- [ ] **Step 2: Replace prints**
- [ ] **Step 3: Verify syntax**

### Task 7: Update `backend/pipeline/characters/vectorize_characters.py`

**Files:**
- Modify: `backend/pipeline/characters/vectorize_characters.py`

- [ ] **Step 1: Inject Logger**
- [ ] **Step 2: Replace prints**
- [ ] **Step 3: Verify syntax**

### Task 8: Update `backend/pipeline/characters/vectorize_vg_characters.py`

**Files:**
- Modify: `backend/pipeline/characters/vectorize_vg_characters.py`

- [ ] **Step 1: Inject Logger**
- [ ] **Step 2: Replace prints**
- [ ] **Step 3: Verify syntax**
