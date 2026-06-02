# Refactor Empty Exception Blocks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `except: pass` and `except Exception: pass` blocks with structured logging across 10 files to improve observability.

**Architecture:** Inject `logging` module and a file-specific logger, then update exception blocks to log warnings with context.

**Tech Stack:** Python, Logging

---

### Task 1: Refactor API Game Views

**Files:**
- Modify: `backend/api/animetix/api/games/archetypist.py`
- Modify: `backend/api/animetix/api/games/blindtest.py`
- Modify: `backend/api/animetix/api/games/classic.py`
- Modify: `backend/api/animetix/api/games/covertest.py`
- Modify: `backend/api/animetix/api/games/emoji.py`
- Modify: `backend/api/animetix/api/games/paradox.py`
- Modify: `backend/api/animetix/api/games/vision.py`

- [ ] **Step 1: Update archetypist.py**
  - Add `import logging`
  - Add `logger = logging.getLogger("animetix." + __name__)`
  - Replace `pass` in `except (CreativeFusion.DoesNotExist, ValueError):`

- [ ] **Step 2: Update blindtest.py**
  - Add `import logging`
  - Add `logger = logging.getLogger("animetix." + __name__)`
  - Replace `pass` in `except Exception:`

- [ ] **Step 3: Update classic.py**
  - Add `import logging`
  - Add `logger = logging.getLogger("animetix." + __name__)`
  - Replace `pass` in `except Exception:`

- [ ] **Step 4: Update covertest.py**
  - Add `import logging`
  - Add `logger = logging.getLogger("animetix." + __name__)`
  - Replace `pass` in `except Exception:`

- [ ] **Step 5: Update emoji.py**
  - Add `import logging`
  - Add `logger = logging.getLogger("animetix." + __name__)`
  - Replace `pass` in `except Exception:`

- [ ] **Step 6: Update paradox.py**
  - Add `import logging`
  - Add `logger = logging.getLogger("animetix." + __name__)`
  - Replace `pass` in `except Exception:`

- [ ] **Step 7: Update vision.py**
  - Add `import logging`
  - Add `logger = logging.getLogger("animetix." + __name__)`
  - Replace `pass` in `except Exception:`

---

### Task 2: Refactor Core Domain Services

**Files:**
- Modify: `backend/core/domain/services/creative/vs_battle_service.py`
- Modify: `backend/core/domain/services/llm_service.py`
- Modify: `backend/core/domain/services/multi_agent_bus.py`

- [ ] **Step 1: Update vs_battle_service.py**
  - Replace `pass` in both `except json.JSONDecodeError:` blocks in `_extract_json`.

- [ ] **Step 2: Update llm_service.py**
  - Replace `pass` in `except ImportError:` in `generate`.

- [ ] **Step 3: Update multi_agent_bus.py**
  - Replace `pass` in `except Exception:` in `_listen_loop` finally block.

---

### Task 3: Verification

- [ ] **Step 1: Check syntax**
  - Run: `python -m py_compile backend/api/animetix/api/games/*.py backend/core/domain/services/*.py backend/core/domain/services/creative/*.py`
  - Expected: No errors.
