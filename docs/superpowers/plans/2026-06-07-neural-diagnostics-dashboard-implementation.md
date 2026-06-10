# Neural Diagnostics Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a workstation-style dashboard to visualize LLM interpretability metrics (entropy, logit lens).

**Architecture:** Hexagonal architecture. Logic resides in `XaiDiagnosticService`. Frontend uses React 19 with specialized visualization components.

**Tech Stack:** React 19, TypeScript, Framer Motion, Django 5, Lucide React.

---

### Task 1: Backend Domain Logic (XAI Service)

**Files:**
- Modify: `backend/core/domain/services/xai_service.py`
- Test: `tests/core/services/test_xai_diagnostics.py`

- [X] **Step 1: Write failing test for diagnostics data generation**

```python
def test_xai_service_generates_logit_lens_simulation():
    # Verify it returns a list of layers, each with token probabilities
    # based on a real InferenceResponse
```

- [X] **Step 2: Implement `get_diagnostics_report` in `XaiDiagnosticService`**
(Should return token-level entropy and a simulated 32-layer logit lens trajectory).

- [X] **Step 3: Run test and verify PASS**

- [X] **Step 4: Commit**

---

### Task 2: Backend API Endpoint

**Files:**
- Modify: `backend/api/animetix/api/labs.py`
- Modify: `backend/api/animetix/urls/api.py`
- Test: `tests/api/test_diagnostics_api.py`

- [X] **Step 1: Implement `NeuralDiagnosticsLabView`**
(POST endpoint that runs inference with `include_logprobs=True` and returns the XAI report).

- [X] **Step 2: Register route `/api/v1/labs/diagnostics/`**

- [X] **Step 3: Verify with integration test**

- [X] **Step 4: Commit**

---

### Task 3: Frontend Hook & Page Skeleton

**Files:**
- Create: `frontend/src/features/labs/hooks/useNeuralDiagnostics.ts`
- Create: `frontend/src/pages/labs/NeuralDiagnosticsPage.tsx`
- Modify: `frontend/src/features/labs/routes/LabRoutes.tsx`

- [X] **Step 1: Implement `useNeuralDiagnostics` hook**
(Uses TanStack Query to call the new API).

- [X] **Step 2: Scaffold `NeuralDiagnosticsPage` with Split Layout**

- [X] **Step 3: Register route `/lab/diagnostics/`**

- [X] **Step 4: Commit**

---

### Task 4: Entropy & Heatmap Components

**Files:**
- Create: `frontend/src/features/labs/components/EntropyBarChart.tsx`
- Create: `frontend/src/features/labs/components/LogitLensHeatmap.tsx`

- [X] **Step 1: Implement `EntropyBarChart`**
(Visualizes per-token uncertainty using dynamic bars).

- [X] **Step 2: Implement `LogitLensHeatmap`**
(Grid visualization showing layer-wise convergence).

- [X] **Step 3: Integrate into `NeuralDiagnosticsPage`**

- [X] **Step 4: Commit**

---

### Task 5: Final Validation

- [X] **Step 1: Verify End-to-End**
1. Navigate to `/lab/diagnostics/`.
2. Enter a prompt.
3. Run diagnostic.
4. Verify bars and heatmap populate with data.
