# The Forge (Speculative Logic) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a speculative logic engine that autonomously generates hypotheses when factual data is missing, leveraging patterns in the Neo4j knowledge graph.

**Architecture:** Add a `ForgeAgent`, update the `RAGState` enum, and integrate a new `SPECULATE` state into the `AgenticRAGService` state machine, triggered by a failure in knowledge acquisition.

**Tech Stack:** Python, Neo4j, Agentic RAG.

---

### Task 1: Update AI Schemas and Prompts

**Files:**
- Modify: `backend/core/domain/entities/ai_schemas.py`
- Modify: `backend/core/domain/services/prompts/prompts.yaml`

- [ ] **Step 1: Add `SPECULATE` to `RAGState`**

```python
class RAGState(str, Enum):
    # ...
    ACQUIRE_KNOWLEDGE = "ACQUIRE_KNOWLEDGE"
    SPECULATE = "SPECULATE"  # Added
    # ...
```

- [ ] **Step 2: Add `forge_speculation` prompt template**

```yaml
forge_speculation:
  template: |
    RÔLE : Détective Expert en Patterns Anime (The Forge).
    TACHE : Génère une hypothèse logique basée sur les patterns du graphe pour combler une lacune de connaissance.

    REQUÊTE UTILISATEUR : '{query}'
    CONTEXTE RÉCOLTÉ (Incomplet) :
    {context}

    MISSION :
    1. Analyse les entités présentes (Studio, Auteur, Genre).
    2. Identifie les comportements passés similaires dans le graphe (ex: cycles de production habituels).
    3. Formule une hypothèse "instruite" et probable.
    4. Cite les patterns spécifiques qui soutiennent ta déduction.

    CONSIGNE CRITIQUE : Commence impérativement par "[SPECULATION]". Ne présente JAMAIS cela comme un fait établi.

    RÉPONDS UNIQUEMENT EN JSON :
    {{
      "hypothesis": "...",
      "rationale": "Patterns identifiés : ...",
      "confidence": 0.0|1.0
    }}
  system_prompt: "Tu es le cerveau spéculatif d'Animetix. Tu transformes les manques de données en déductions expertes."
```

- [ ] **Step 3: Commit**

```bash
git add backend/core/domain/entities/ai_schemas.py backend/core/domain/services/prompts/prompts.yaml
git commit -m "feat: add SPECULATE state and forge prompt"
```

---

### Task 2: Create Forge Agent

**Files:**
- Create: `backend/core/domain/services/rag/agents/forge.py`

- [ ] **Step 1: Implement `ForgeAgent` class**
  - Accept `llm_service: LLMService`, `prompt_manager: PromptManager`, and `neo4j_manager: Neo4jManager` in the constructor.
  - Implement `generate_hypothesis(self, query: str, context: str) -> Optional[Dict[str, Any]]`:
    - Calls `self.prompt_manager.get_prompt("forge_speculation", query=query, context=context)`.
    - Calls `self.llm_service.generate(..., use_slm=True)`.
    - Parses the JSON output to extract `hypothesis`, `rationale`, and `confidence`.
  - Implement `_fetch_patterns(self, entities: List[str])`:
    - (Optional enhancement) Calls Neo4j to find historical data for those entities to enrich the prompt context.

- [ ] **Step 2: Commit**

```bash
git add backend/core/domain/services/rag/agents/forge.py
git commit -m "feat: implement ForgeAgent for pattern-based speculation"
```

---

### Task 3: Integrate SPECULATE State in AgenticRAGService

**Files:**
- Modify: `backend/core/domain/services/agentic_rag_service.py`
- Modify: `backend/api/animetix/containers.py`

- [ ] **Step 1: Update `AgenticRAGService` dependencies**
  - Accept `forge: ForgeAgent` in the constructor.

- [ ] **Step 2: Implement `_handle_speculate(self, ctx: RAGContext)`**
  - Yield thought: "[The Forge] Lancement du moteur de spéculation logique...".
  - Call `ForgeAgent.generate_hypothesis`.
  - If hypothesis generated:
    - Yield thought: f"[The Forge] Hypothèse générée : {res['hypothesis']} (Basé sur : {res['rationale']})".
    - Append hypothesis to `ctx.truth_path` with a clear speculative disclaimer.
  - Transition: `ctx.current_state = RAGState.SYNTHESIZE`.

- [ ] **Step 3: Update Transition Triggers**
  - In `_handle_acquire_knowledge`: if Librarian returns no data, transition to `SPECULATE` instead of giving up.
  - Ensure the main `while` loop handles `RAGState.SPECULATE`.

- [ ] **Step 4: Update `Container`**
  - Register `ForgeAgent` and inject it into the `agentic_rag` service.

- [ ] **Step 5: Commit**

```bash
git add backend/core/domain/services/agentic_rag_service.py backend/api/animetix/containers.py
git commit -m "feat: integrate SPECULATE state into AgenticRAG orchestrator"
```

---

### Task 4: End-to-End Verification

**Files:**
- Create: `tests/core/test_forge_agent.py`

- [ ] **Step 1: Write integration test**
  - Mock Librarian to return no data.
  - Mock Forge to return a reasoned hypothesis about a release date.
  - Run `AgenticRAGService.plan_and_solve_stream`.
  - Assert that `SPECULATE` was reached.
  - Assert that the final answer contains the `[SPECULATION]` tag and the hypothesis.

- [ ] **Step 2: Run test**

Run: `pytest tests/core/test_forge_agent.py -v`

- [ ] **Step 3: Commit final changes**

```bash
git add .
git commit -m "docs: finalize The Forge (Speculative Logic) integration"
```
