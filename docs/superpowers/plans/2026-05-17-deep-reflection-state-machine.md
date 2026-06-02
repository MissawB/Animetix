# Deep Reflection State Machine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the linear RAG pipeline into a state-machine orchestrator where the Judge agent can trigger re-planning, re-searching, or re-drafting based on output quality.

**Architecture:** Implement a LangGraph-style state machine in `AgenticRAGService` using an explicit `State` enum and a Judge-based router.

**Tech Stack:** Python, Pydantic, Agentic RAG.

---

### Task 1: Update AI Schemas for State Machine Routing

**Files:**
- Modify: `backend/core/domain/entities/ai_schemas.py`

- [ ] **Step 1: Add `JudgeAction` enum and update `JudgeEvaluation`**

```python
from enum import Enum

class JudgeAction(str, Enum):
    APPROVE = "APPROVE"
    REWRITE = "REWRITE"
    RESEARCH_MORE = "RESEARCH_MORE"
    REPLAN = "REPLAN"

class JudgeEvaluation(BaseModel):
    faithfulness_score: float
    relevancy_score: float
    hallucination_detected: bool
    reasoning: str
    is_reliable: bool
    next_action: JudgeAction  # Added
```

- [ ] **Step 2: Commit**

```bash
git add backend/core/domain/entities/ai_schemas.py
git commit -m "feat: add next_action to JudgeEvaluation schema"
```

---

### Task 2: Update Judge Prompt for Routing Logic

**Files:**
- Modify: `backend/core/domain/services/prompts/prompts.yaml`

- [ ] **Step 1: Update `answer_judge` template**

```yaml
answer_judge:
  template: |
    # ... existing prompt ...
    
    MISSIONS :
    1. FAITHFULNESS : ...
    2. RELEVANCY : ...
    3. ROUTING : Détermine la prochaine action ('next_action') :
       - 'APPROVE' : Tout est parfait.
       - 'REWRITE' : L'info est là mais mal formulée ou contient une petite erreur.
       - 'RESEARCH_MORE' : Il manque des faits cruciaux pour répondre.
       - 'REPLAN' : La stratégie de recherche était totalement hors-sujet.

    RÉPONDS UNIQUEMENT EN JSON :
    {
      "faithfulness_score": 0.0|1.0,
      "relevancy_score": 0.0|1.0,
      "hallucination_detected": true|false,
      "reasoning": "...",
      "is_reliable": true|false,
      "next_action": "APPROVE"|"REWRITE"|"RESEARCH_MORE"|"REPLAN"
    }
```

- [ ] **Step 2: Commit**

```bash
git add backend/core/domain/services/prompts/prompts.yaml
git commit -m "feat: update Judge prompt to support deep routing actions"
```

---

### Task 3: Refactor AgenticRAGService to State Machine

**Files:**
- Modify: `backend/core/domain/services/agentic_rag_service.py`

- [ ] **Step 1: Implement the State Machine Loop**

```python
    def plan_and_solve_stream(self, query: str, media_type: str, user_id: Optional[str] = None) -> Generator[Dict, None, None]:
        # ... setup (complexity, cache, memories) ...
        
        current_state = "PLAN"
        max_iterations = 5
        iteration = 0
        plan = None
        truth_path = ""
        last_answer = ""
        correction_feedback = None

        while current_state != "FINALIZE" and iteration < max_iterations:
            iteration += 1
            
            if current_state == "PLAN":
                # Execute Planner
                plan = self.planner.plan(...)
                current_state = "RESEARCH"
                
            elif current_state == "RESEARCH":
                # Execute Search + Scout
                raw_context = self._execute_search(plan, media_type)
                truth_path = self.scout.find_truth_path(query, plan, raw_context)
                current_state = "SYNTHESIZE"
                
            elif current_state == "SYNTHESIZE":
                # Execute Synthesizer
                # (yield tokens and update last_answer)
                current_state = "JUDGE"
                
            elif current_state == "JUDGE":
                # Execute Judge
                evaluation = self.judge.evaluate(query, truth_path, last_answer)
                action = evaluation.next_action
                
                if action == "APPROVE":
                    current_state = "FINALIZE"
                elif action == "REWRITE":
                    correction_feedback = evaluation.reasoning
                    current_state = "SYNTHESIZE"
                elif action == "RESEARCH_MORE":
                    current_state = "RESEARCH"
                elif action == "REPLAN":
                    current_state = "PLAN"
        
        # ... store results ...
```

- [ ] **Step 2: Commit**

```bash
git add backend/core/domain/services/agentic_rag_service.py
git commit -m "feat: implement deep reflection state machine loop in AgenticRAG"
```

---

### Task 4: End-to-End Verification

**Files:**
- Create: `tests/core/test_rag_state_machine.py`

- [ ] **Step 1: Write integration test for "RESEARCH_MORE" loop**

- [ ] **Step 2: Verify on complex query using `scripts/verify_thinking_in_action.py`**

- [ ] **Step 3: Commit final changes**

```bash
git add .
git commit -m "docs: finalize Deep Reflection State Machine integration"
```
