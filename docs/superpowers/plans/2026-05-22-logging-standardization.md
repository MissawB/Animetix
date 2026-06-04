# Standardization of Python Logging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Standardize logging across all pipeline files by replacing `print()` calls with `logging` and ensuring consistent logger naming.

**Architecture:** Each file will use a logger named `animetix.<module_name>` to allow fine-grained log control and integration with the broader system's logging configuration.

**Tech Stack:** Python built-in `logging` module.

---

### Task 1: Refactor `backend/pipeline/advanced_scrapers.py`

**Files:**
- Modify: `backend/pipeline/advanced_scrapers.py`

- [ ] **Step 1: Replace print with logger.warning**
Replace the Django setup warning `print` with `logger.warning`.

- [ ] **Step 2: Verify syntax**
Run: `python -m py_compile backend/pipeline/advanced_scrapers.py`

---

### Task 2: Refactor `backend/pipeline/characters/ingest_characters.py`

**Files:**
- Modify: `backend/pipeline/characters/ingest_characters.py`

- [ ] **Step 1: Add logging import and logger initialization**
Add `import logging` and `logger = logging.getLogger("animetix." + __name__)` at the top.

- [ ] **Step 2: Replace all print calls with logger methods**
Replace `print` with `logger.info`, `logger.error`, or `logger.warning` appropriately.

- [ ] **Step 3: Verify syntax**
Run: `python -m py_compile backend/pipeline/characters/ingest_characters.py`

---

### Task 3: Refactor `backend/pipeline/chroma_client.py`

**Files:**
- Modify: `backend/pipeline/chroma_client.py`

- [ ] **Step 1: Add logging import and logger initialization**
Add `import logging` and `logger = logging.getLogger("animetix." + __name__)` at the top.

- [ ] **Step 2: Replace all print calls with logger.info**
Replace `print(...)` with `logger.info(...)`.

- [ ] **Step 3: Verify syntax**
Run: `python -m py_compile backend/pipeline/chroma_client.py`

---

### Task 4: Refactor `backend/pipeline/neo4j_sync.py`

**Files:**
- Modify: `backend/pipeline/neo4j_sync.py`

- [ ] **Step 1: Add logging import and logger initialization**
Add `import logging` and `logger = logging.getLogger("animetix." + __name__)` at the top.

- [ ] **Step 2: Replace all print calls with logger methods**
Replace `print` with `logger.info` or `logger.warning`.

- [ ] **Step 3: Verify syntax**
Run: `python -m py_compile backend/pipeline/neo4j_sync.py`

---

### Task 5: Refactor `backend/pipeline/neo4j_client.py`

**Files:**
- Modify: `backend/pipeline/neo4j_client.py`

- [ ] **Step 1: Update logger name for consistency**
Change `logger = logging.getLogger("animetix.neo4j")` to `logger = logging.getLogger("animetix." + __name__)`.

- [ ] **Step 2: Restore and use logger for connection success**
Uncomment and use `logger.info` for the connection message.

- [ ] **Step 3: Verify syntax**
Run: `python -m py_compile backend/pipeline/neo4j_client.py`

---

### Task 6: Refactor `backend/pipeline/expert_enrichment.py`

**Files:**
- Modify: `backend/pipeline/expert_enrichment.py`

- [ ] **Step 1: Add logging import and logger initialization**
Add `import logging` and `logger = logging.getLogger("animetix." + __name__)` at the top.

- [ ] **Step 2: Replace all print calls with logger methods**
Replace `print` with `logger.info`, `logger.error`, or `logger.warning`.

- [ ] **Step 3: Verify syntax**
Run: `python -m py_compile backend/pipeline/expert_enrichment.py`

---

### Task 7: Refactor `backend/pipeline/specialized_scrapers.py`

**Files:**
- Modify: `backend/pipeline/specialized_scrapers.py`

- [ ] **Step 1: Replace print with logger.warning**
Replace the Django setup warning `print` with `logger.warning`.

- [ ] **Step 2: Verify syntax**
Run: `python -m py_compile backend/pipeline/specialized_scrapers.py`

---

### Task 8: Refactor `backend/pipeline/enrich_db_scraper.py`

**Files:**
- Modify: `backend/pipeline/enrich_db_scraper.py`

- [ ] **Step 1: Replace print with logger.warning**
Replace the Django setup warning `print` with `logger.warning`.

- [ ] **Step 2: Verify syntax**
Run: `python -m py_compile backend/pipeline/enrich_db_scraper.py`

---

### Task 9: Refactor `backend/pipeline/expert_scrapers.py`

**Files:**
- Modify: `backend/pipeline/expert_scrapers.py`

- [ ] **Step 1: Replace print with logger.warning**
Replace the Django setup warning `print` with `logger.warning`.

- [ ] **Step 2: Verify syntax**
Run: `python -m py_compile backend/pipeline/expert_scrapers.py`
