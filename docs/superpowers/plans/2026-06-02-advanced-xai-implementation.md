# Advanced XAI (Semantic Middleware) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a comprehensive explainability layer that combines internal LLM diagnostics with RAG attribution reasoning.

**Architecture:** A "Semantic Middleware" pattern where a `XaiCollector` captures real-time workflow events, which are then aggregated by `XaiDiagnosticService` into a unified `XaiReport`.

**Tech Stack:** Python, Pydantic, FastAPI, PyTorch (for internal diagnostics).

---

### Task 1: Domain Entities & Schemas

**Files:**
- Modify: `backend/core/domain/entities/ai_schemas.py`

- [ ] **Step 1: Add XAI Entities to `ai_schemas.py`**

```python
class DocumentAttribution(BaseModel):
    document_id: str
    title: str
    relevance_score: float
    contribution_weight: float = 0.0

class ModelDiagnostics(BaseModel):
    attention_heatmap: List[List[float]] = Field(default_factory=list)
    top_influential_tokens: List[str] = Field(default_factory=list)
    logit_lens_trajectory: List[Dict[str, Any]] = Field(default_factory=list)

class XaiReport(BaseModel):
    query_intent: str = ""
    retrieval_attribution: List[DocumentAttribution] = Field(default_factory=list)
    internal_diagnostics: Optional[ModelDiagnostics] = None
    uncertainty: Dict[str, Any] = Field(default_factory=list)
    agent_trace: List[Dict[str, Any]] = Field(default_factory=list)
    final_confidence: float = 0.0
```

- [ ] **Step 2: Update `RAGContext` to include a `XaiCollector` reference (or equivalent)**
Actually, we'll pass the collector explicitly in the workflow.

- [ ] **Step 3: Commit**

```bash
git add backend/core/domain/entities/ai_schemas.py
git commit -m "feat(xai): add domain entities for advanced xai"
```

### Task 2: XaiCollector Implementation

**Files:**
- Modify: `backend/core/domain/services/xai_service.py`

- [ ] **Step 1: Write the failing test for `XaiCollector`**
Create `tests/core/test_xai_collector.py`.

- [ ] **Step 2: Implement `XaiCollector` in `xai_service.py`**

```python
class XaiCollector:
    def __init__(self):
        self.steps = []
        self.retrieved_docs = []
        self.intent = ""

    def log_intent(self, intent: str):
        self.intent = intent

    def log_retrieval(self, docs: List[Dict]):
        self.retrieved_docs = docs

    def log_agent_thought(self, agent: str, thought: str):
        self.steps.append({"agent": agent, "thought": thought})
```

- [ ] **Step 3: Commit**

```bash
git add backend/core/domain/services/xai_service.py tests/core/test_xai_collector.py
git commit -m "feat(xai): implement XaiCollector"
```

### Task 3: RAGWorkflowManager Integration

**Files:**
- Modify: `backend/core/domain/services/rag_workflow_manager.py`

- [ ] **Step 1: Update `run_workflow` to accept `xai_collector`**

- [ ] **Step 2: Add logging hooks in `_handle_plan`, `_handle_research`, etc.**
Example in `_handle_plan`: `if xai_collector: xai_collector.log_intent(ctx.plan.reasoning)`

- [ ] **Step 3: Commit**

```bash
git add backend/core/domain/services/rag_workflow_manager.py
git commit -m "feat(xai): integrate XaiCollector into RAGWorkflowManager"
```

### Task 4: Upgraded XaiDiagnosticService

**Files:**
- Modify: `backend/core/domain/services/xai_service.py`

- [ ] **Step 1: Implement `generate_advanced_report`**
This method will take the `xai_collector` and raw diagnostics from `InferencePort` to build the `XaiReport`.

- [ ] **Step 2: Fix key mismatches between Service and Adapter**
Service expects `logit_lens_trend`, Adapter returns `logit_lens`. Align them to `logit_lens_trajectory`.

- [ ] **Step 3: Commit**

```bash
git add backend/core/domain/services/xai_service.py
git commit -m "feat(xai): upgrade XaiDiagnosticService to orchestrate hybrid reports"
```

### Task 5: Adapter Alignment (UnifiedInferenceAdapter)

**Files:**
- Modify: `backend/adapters/inference/unified_inference_adapter.py`

- [ ] **Step 1: Align `get_diagnostics` output keys with `XaiReport`**
Rename `logit_lens` to `logit_lens_trajectory` in the returned dict.

- [ ] **Step 2: Commit**

```bash
git add backend/adapters/inference/unified_inference_adapter.py
git commit -m "fix(xai): align adapter diagnostic keys with domain schemas"
```

### Task 6: API Exposure & Verification

**Files:**
- Modify: `backend/core/domain/services/agentic_rag_service.py`
- Modify: `backend/api/animetix/containers/agentic.py`

- [ ] **Step 1: Update `AgenticRAGService` to return `XaiReport`**

- [ ] **Step 2: Run verification tests**
Run `pytest tests/core/test_xai_service.py` and a smoke test for RAG.

- [ ] **Step 3: Commit**

```bash
git add backend/core/domain/services/agentic_rag_service.py backend/api/animetix/containers/agentic.py
git commit -m "feat(xai): expose advanced xai report in agentic rag service"
```
