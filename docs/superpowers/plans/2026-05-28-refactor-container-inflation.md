# Refactor Container Inflation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the monolithic `backend/api/animetix/containers.py` (>750 lines) into modular domain-specific containers to improve maintainability and follow SOLID principles.

**Architecture:** We are using `dependency-injector` modules. The main `Container` will aggregate sub-containers for Infrastructure, Persistence, Inference, Agentic RAG, and Core Services using `providers.Container`.

**Tech Stack:** Python, `dependency-injector`.

---

### Task 1: Create Container Modules

**Files:**
- Create: `backend/api/animetix/containers/__init__.py`
- Create: `backend/api/animetix/containers/infrastructure.py`
- Create: `backend/api/animetix/containers/persistence.py`
- Create: `backend/api/animetix/containers/inference.py`
- Create: `backend/api/animetix/containers/agentic.py`
- Create: `backend/api/animetix/containers/core_services.py`

- [ ] **Step 1: Implement `infrastructure.py`**
  Move `config`, `prompt_manager`, `translation_service`, `obs_service`, `usage_port`, `notification_port`, `web_search`.

- [ ] **Step 2: Implement `persistence.py`**
  Move `repository`, `django_repository`, `graph_persistence_port`, `feedback_adapter`, `eval_adapter`, `gold_dataset_adapter`, `semantic_cache_adapter`, `colbert_adapter`.

- [ ] **Step 3: Implement `inference.py`**
  Move all inference adapters (Local, Unified, BrainAPI, etc.) and the `inference_engine` (Fallback).

- [ ] **Step 4: Implement `agentic.py`**
  Move all RAG agents (Scout, Critic, etc.), `rag_workflow_manager`, and `agentic_rag`.

- [ ] **Step 5: Implement `core_services.py`**
  Move domain services like `GameService`, `AchievementDomainService`, and specialized simulators (`LiquidNeuralNetwork`, `QuantumCognitiveModel`, etc.).

- [ ] **Step 6: Implement `__init__.py`**
  Define the main `Container` class that pulls all sub-containers.

```python
from dependency_injector import containers, providers
from .infrastructure import InfrastructureContainer
from .persistence import PersistenceContainer
from .inference import InferenceContainer
from .agentic import AgenticContainer
from .core_services import CoreServicesContainer

class Container(containers.DeclarativeContainer):
    infrastructure = providers.Container(InfrastructureContainer)
    persistence = providers.Container(PersistenceContainer)
    inference = providers.Container(InferenceContainer, infrastructure=infrastructure, persistence=persistence)
    agentic = providers.Container(AgenticContainer, infrastructure=infrastructure, persistence=persistence, inference=inference)
    core = providers.Container(CoreServicesContainer, infrastructure=infrastructure, persistence=persistence, inference=inference, agentic=agentic)

container = Container()

def get_container():
    return container
```

- [ ] **Step 7: Commit**

```bash
git add backend/api/animetix/containers/
git commit -m "refactor: modularize DI container into domain-specific sub-containers"
```

### Task 2: Replace Monolithic Container and Update Wiring

**Files:**
- Modify: `backend/api/animetix/containers.py` (Delete or replace content)
- Modify: `backend/api/animetix/apps.py` (Verify wiring if needed)

- [ ] **Step 1: Replace `backend/api/animetix/containers.py`**
  It should now just export `get_container` and `Container` from the new package to maintain backward compatibility.

```python
from .containers import Container, get_container
```

- [ ] **Step 2: Verify imports in other files**
  Since we are using `get_container()`, existing code like `from .containers import get_container` should still work.

- [ ] **Step 3: Commit**

```bash
git add backend/api/animetix/containers.py
git commit -m "refactor: replace monolithic containers.py with modular package export"
```
