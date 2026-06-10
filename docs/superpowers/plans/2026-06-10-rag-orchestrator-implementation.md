# RAG Workflow Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor `RAGWorkflowManager` into a decoupled orchestrator pattern with atomic state processors to improve maintainability and adherence to hexagonal architecture.

**Architecture:** Implement a base `StateProcessor` class and concrete processors for each RAG state. A new `RAGOrchestrator` will handle state transitions.

**Tech Stack:** Python 3.11+, Pydantic (v2), Pytest

---

### Task 1: Define `StateProcessor` Interface

**Files:**
- Create: `backend/core/domain/services/rag/processors/base.py`

- [ ] **Step 1: Write `StateProcessor` base class**

```python
from abc import ABC, abstractmethod
from backend.core.entities.ai_schemas import RAGContext, RAGState

class StateProcessor(ABC):
    @abstractmethod
    def process(self, ctx: RAGContext) -> RAGState:
        """Processes the state and returns the next RAGState."""
        pass
```

- [ ] **Step 2: Commit**
```bash
git add backend/core/domain/services/rag/processors/base.py
git commit -m "feat: add StateProcessor base class"
```

### Task 2: Implement Atomic State Processors

**Files:**
- Create: `backend/core/domain/services/rag/processors/plan_processor.py`
- Modify: `backend/core/domain/services/rag_workflow_manager.py` (extract logic)

- [ ] **Step 1: Implement `PlanProcessor`**

```python
from backend.core.domain.services.rag.processors.base import StateProcessor
from backend.core.entities.ai_schemas import RAGContext, RAGState

class PlanProcessor(StateProcessor):
    def __init__(self, planner):
        self.planner = planner

    def process(self, ctx: RAGContext) -> RAGState:
        # Move logic from RAGWorkflowManager._handle_plan here
        plan = self.planner.plan(ctx.query, ctx.memories)
        ctx.plan = plan
        if plan.requires_saga:
            return RAGState.SAGA_LOOKUP
        elif plan.requires_graph:
            return RAGState.GRAPH_EXPLORE
        return RAGState.RESEARCH
```

- [ ] **Step 2: Run tests**
Ensure existing tests still pass.

- [ ] **Step 3: Commit**
```bash
git add backend/core/domain/services/rag/processors/plan_processor.py
git commit -m "feat: implement PlanProcessor"
```

*(Repeat for other processors: ResearchProcessor, etc.)*

### Task 3: Implement `RAGOrchestrator`

**Files:**
- Create: `backend/core/domain/services/rag_orchestrator.py`

- [ ] **Step 1: Write `RAGOrchestrator`**

```python
from backend.core.entities.ai_schemas import RAGContext, RAGState

class RAGOrchestrator:
    def __init__(self, processors: dict[RAGState, StateProcessor]):
        self.processors = processors

    def run_workflow(self, ctx: RAGContext):
        while ctx.current_state not in [RAGState.FINALIZE, RAGState.FAILED]:
            processor = self.processors[ctx.current_state]
            ctx.current_state = processor.process(ctx)
```

- [ ] **Step 2: Commit**
```bash
git add backend/core/domain/services/rag_orchestrator.py
git commit -m "feat: implement RAGOrchestrator"
```

### Task 4: Integration and Cleanup

- [ ] **Step 1: Update DI container**
Modify `backend/api/animetix/containers.py` to register the `RAGOrchestrator` and its processors instead of `RAGWorkflowManager`.

- [ ] **Step 2: Remove old `RAGWorkflowManager`**
Delete `backend/core/domain/services/rag_workflow_manager.py` after verification.

- [ ] **Step 3: Commit**
```bash
git add backend/api/animetix/containers.py
git rm backend/core/domain/services/rag_workflow_manager.py
git commit -m "refactor: replace RAGWorkflowManager with RAGOrchestrator"
```
