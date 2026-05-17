# Design Spec: Deep Reflection State Machine (RAG-SC)

**Date:** 2026-05-17
**Status:** Draft
**Topic:** Implementing a SOTA 2026 Self-Correction State Machine in Agentic RAG

## 1. Problem Statement
The current linear RAG pipeline is prone to "one-shot failure". If the initial retrieval is poor or the synthesis hallucinates, the system can only perform a shallow correction. To achieve true expert-level reliability, the system needs to be able to go back to the planning or research stage based on high-level evaluation.

## 2. Proposed Solution
Transform `AgenticRAGService` into a **State Machine Router**. The `Judge` agent is promoted to "System Router", evaluating every output and deciding the next state.

## 3. State Machine Architecture

### A. States
1. **ANALYZE**: Complexity assessment and initial budget allocation.
2. **PLAN**: Strategic planning (Searcher Planner).
3. **RESEARCH**: Vector search (ChromaDB), Graph traversal (Neo4j), or Web search.
4. **SCOUT**: Context distillation (Truth Path).
5. **SYNTHESIZE**: Final answer drafting.
6. **JUDGE/ROUTE**: Quality audit and next-step decision.
7. **FINALIZE**: Cache storage and final return.

### B. Router Logic (The Judge)
The `Judge` will now output a `next_action`:
- `APPROVE` -> Move to **FINALIZE**.
- `REWRITE` -> Move to **SYNTHESIZE** with feedback (current behavior).
- `RESEARCH_MORE` -> Move back to **RESEARCH** with specific missing info tags.
- `REPLAN` -> Move back to **PLAN** if the strategy was fundamentally flawed.

## 4. Implementation Details

### A. Schemas (`src/core/domain/entities/ai_schemas.py`)
- Update `JudgeEvaluation` to include `next_action` (Enum: `APPROVE`, `REWRITE`, `RESEARCH_MORE`, `REPLAN`).

### B. Prompts (`src/core/domain/services/prompts/prompts.yaml`)
- Update `answer_judge` to force the `next_action` output based on reasoning.

### C. Orchestrator (`src/core/domain/services/agentic_rag_service.py`)
- Refactor `plan_and_solve_stream` into a `while` loop (max iterations: 5) handling the state transitions.

## 5. Success Criteria
- The system can automatically switch from Local to Web search if the Judge finds local data insufficient.
- Multi-hop graph queries that failed distillation can be re-attempted with a different strategy.
- Hallucinations trigger a hard "REWRITE" or "RESEARCH" loop.
- **Animetix Score Improvement**: Estimated +20% on complex architectural queries.
