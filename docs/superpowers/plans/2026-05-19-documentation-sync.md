# Documentation Synchronization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Synchronize README.md, ARCHITECTURE.md, and FULL_GUIDE.md with the current SOTA 2026 codebase state.

**Architecture:** Surgical updates to documentation files to reflect the "Atomic & Hexagonal" reality, PgVector primary storage, and modularized view structure.

**Tech Stack:** Markdown, Git.

---

### Task 1: Update README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update Architecture & Tech Stack section**
    Update to reflect PgVector as primary and modularized structure.
    
- [ ] **Step 2: Update Project Structure tree**
    Ensure `backend/api/animetix/views/` is correctly represented.

- [ ] **Step 3: Update Manual Development Setup**
    Include `python backend/api/manage.py sync_catalog` and other necessary seeds.

- [ ] **Step 4: Commit README changes**
    `git add README.md && git commit -m "docs: sync README with current codebase state"`

### Task 2: Update ARCHITECTURE.md

**Files:**
- Modify: `docs/ARCHITECTURE.md`

- [ ] **Step 1: Update Persistence section**
    Detail `UnifiedRepositoryAdapter` and PgVector HNSW indexing.

- [ ] **Step 2: Update Refactoring Status**
    Move "Modularization of UI Logic" and "views.py refactoring" to completed or advanced state.
    Set "Utils Decoupling" as high priority.

- [ ] **Step 3: Add Dependency Injection Container section**
    Explain the `Container` class in `backend/api/animetix/containers.py`.

- [ ] **Step 4: Commit ARCHITECTURE changes**
    `git add docs/ARCHITECTURE.md && git commit -m "docs: update architecture specs and refactoring priorities"`

### Task 3: Update FULL_GUIDE.md

**Files:**
- Modify: `docs/FULL_GUIDE.md`

- [ ] **Step 1: Update Agentic RAG workflow**
    Detail the `Plan -> Search -> Synthesize` cognitive loop.

- [ ] **Step 2: Add Neuro-Symbolic & Paradox Quest section**
    Mention Z3 solver and neuro-symbolic reasoning.

- [ ] **Step 3: Add Spatial Computing & Vision section**
    Include Voice Cloning, SigLIP, and Qwen-VL details.

- [ ] **Step 4: Commit FULL_GUIDE changes**
    `git add docs/FULL_GUIDE.md && git commit -m "docs: expand technical guide with advanced AI services"`

### Task 4: Final Verification

- [ ] **Step 1: Verify all paths and terms**
    Check that all class names and file paths in docs match the filesystem.
    
- [ ] **Step 2: Final commit for documentation synchronization**
    `git status`
