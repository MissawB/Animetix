# Domain Service Sanitization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor domain services to enforce dependency injection, improve error handling with domain exceptions, and consolidate Akinetix-related services.

**Architecture:** Moving from "hybrid" instantiations in constructors to pure Dependency Injection managed by the container. Consolidating probabilistic engine logic into the high-level Akinetix service.

**Tech Stack:** Python 3.x, Dependency-Injector, Numpy, Pydantic.

---

### Task 1: AgenticRAGService Sanitization

**Files:**
- Modify: `backend/core/domain/services/agentic_rag_service.py`

- [ ] **Step 1: Update __init__ to enforce DI**
  Remove all `or Class(...)` default instantiations for specialized agents and services.
  
- [ ] **Step 2: Replace generic exceptions**
  Search for `RuntimeError`, `TimeoutError`, and generic `except:` blocks.
  Replace with `InfrastructureError`, `InferenceError`, or `ParsingError`.
  Update `plan_and_solve_stream` to catch `AnimetixError` instead of generic errors.

- [ ] **Step 3: Verify syntax**
  Run: `python -m py_compile backend/core/domain/services/agentic_rag_service.py`

### Task 2: Akinetix Services Consolidation

**Files:**
- Modify: `backend/core/domain/services/akinetix_service.py`
- Modify: `backend/core/domain/services/akinetix_rl_service.py`
- Modify: `backend/core/domain/services/akinetix_rl_env.py`
- Delete: `backend/core/domain/services/akinetix_classical_service.py`

- [ ] **Step 1: Merge ClassicalAkinetixService into AkinetixService**
  - Rename `AkinetixDomainService` to `AkinetixService` in `akinetix_service.py`.
  - Copy logic from `ClassicalAkinetixService` (from `akinetix_classical_service.py`) into `AkinetixService`.
  - Update `start_new_game` and `process_answer` to use the internal merged logic instead of an external engine.

- [ ] **Step 2: Rename AkinetixRLDomainService**
  - Rename `AkinetixRLDomainService` to `AkinetixRLService` in `akinetix_rl_service.py`.

- [ ] **Step 3: Clean up akinetix_rl_env.py**
  - Remove the `AkinetixRLService` class definition to avoid naming collisions. Keep `AkinetixRLEnvironment`.

- [ ] **Step 4: Delete the old classical service file**
  - `rm backend/core/domain/services/akinetix_classical_service.py`

### Task 3: Other Services DI Cleanup

**Files:**
- Modify: `backend/core/domain/services/game_service.py`
- Modify: `backend/core/domain/services/advanced_rag_service.py`

- [ ] **Step 1: Update GameService __init__**
  Remove `or SimilarityService(repository)` and `or UndercoverService(...)`. Enforce DI.

- [ ] **Step 2: Update AdvancedRAGService __init__**
  Remove `or ...` for `prompt_manager`.

- [ ] **Step 3: Sanitize exceptions in AdvancedRAGService**
  Replace `except Exception` with specific domain errors where possible.

### Task 4: Container Wiring Update

**Files:**
- Modify: `backend/api/animetix/containers.py`

- [ ] **Step 1: Update imports**
  Reflect the renaming of services and removal of old files.

- [ ] **Step 2: Add missing Agent providers**
  Add providers for `SearchPlanner`, `ResponseCritic`, `ResponseSynthesizer`, `ResponseJudge`, `ScoutAgent`.

- [ ] **Step 3: Update agentic_rag provider**
  Inject all missing agents into the `agentic_rag` singleton.

- [ ] **Step 4: Update Akinetix and GameService providers**
  Ensure they match the new class names and required dependencies.

### Task 5: Final Validation

- [ ] **Step 1: Syntax check all modified files**
  
- [ ] **Step 2: Run container instantiation test**
  Create a small script to try to get `agentic_rag` and `akinetix_service` from the container.
