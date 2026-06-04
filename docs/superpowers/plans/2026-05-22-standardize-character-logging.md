# Standardize Python Logging in Character Pipeline

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all `print()` calls with standardized `logging` calls across 6 files in `backend/pipeline/characters/`.

**Architecture:** Inject a logger instance named `animetix.<module_name>` in each file and map emojis/status to appropriate log levels (info, error, warning).

**Tech Stack:** Python standard `logging` library.

---

### Task 1: Refactor `backend/pipeline/characters/ingest_characters.py`

**Files:**
- Modify: `backend/pipeline/characters/ingest_characters.py`

- [ ] **Step 1: Inject Logger and replace prints**
    - Add `import logging`
    - Add `logger = logging.getLogger("animetix." + __name__)`
    - Replace prints with `logger.info`, `logger.error`, `logger.warning`.

- [ ] **Step 2: Verify syntax**
    Run: `python -m py_compile backend/pipeline/characters/ingest_characters.py`

### Task 2: Refactor `backend/pipeline/characters/ingest_vg_characters.py`

**Files:**
- Modify: `backend/pipeline/characters/ingest_vg_characters.py`

- [ ] **Step 1: Inject Logger and replace prints**
    - Add `import logging`
    - Add `logger = logging.getLogger("animetix." + __name__)`
    - Replace prints with `logger.info`, `logger.error`.

- [ ] **Step 2: Verify syntax**
    Run: `python -m py_compile backend/pipeline/characters/ingest_vg_characters.py`

### Task 3: Refactor `backend/pipeline/characters/refine_characters.py`

**Files:**
- Modify: `backend/pipeline/characters/refine_characters.py`

- [ ] **Step 1: Inject Logger and replace prints**
    - Add `import logging`
    - Add `logger = logging.getLogger("animetix." + __name__)`
    - Replace prints with `logger.info`, `logger.error`, `logger.warning`.

- [ ] **Step 2: Verify syntax**
    Run: `python -m py_compile backend/pipeline/characters/refine_characters.py`

### Task 4: Refactor `backend/pipeline/characters/train_vibe_characters.py`

**Files:**
- Modify: `backend/pipeline/characters/train_vibe_characters.py`

- [ ] **Step 1: Inject Logger and replace prints**
    - Add `logger = logging.getLogger("animetix." + __name__)`
    - Replace prints with `logger.info`.

- [ ] **Step 2: Verify syntax**
    Run: `python -m py_compile backend/pipeline/characters/train_vibe_characters.py`

### Task 5: Refactor `backend/pipeline/characters/vectorize_characters.py`

**Files:**
- Modify: `backend/pipeline/characters/vectorize_characters.py`

- [ ] **Step 1: Inject Logger and replace prints**
    - Add `import logging`
    - Add `logger = logging.getLogger("animetix." + __name__)`
    - Replace prints with `logger.info`, `logger.error`, `logger.warning`.

- [ ] **Step 2: Verify syntax**
    Run: `python -m py_compile backend/pipeline/characters/vectorize_characters.py`

### Task 6: Refactor `backend/pipeline/characters/vectorize_vg_characters.py`

**Files:**
- Modify: `backend/pipeline/characters/vectorize_vg_characters.py`

- [ ] **Step 1: Inject Logger and replace prints**
    - Add `import logging`
    - Add `logger = logging.getLogger("animetix." + __name__)`
    - Replace prints with `logger.info`, `logger.error`, `logger.warning`.

- [ ] **Step 2: Verify syntax**
    Run: `python -m py_compile backend/pipeline/characters/vectorize_vg_characters.py`
