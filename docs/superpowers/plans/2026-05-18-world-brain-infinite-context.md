# World-Brain (Top-Down Hierarchy) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a 3-tier hierarchical memory (Saga, Episode, Fact) to handle long-running franchises with global coherence.

**Architecture:** Add a `SagaAgent`, update Neo4j with `Saga` nodes, and refactor the `AgenticRAGService` orchestrator to support a cascading `SAGA_LOOKUP` state.

**Tech Stack:** Python, Neo4j, Agentic RAG.

---

### Task 1: Update Neo4j Client for Saga Support

**Files:**
- Modify: `backend/pipeline/neo4j_client.py`

- [ ] **Step 1: Add method to sync Sagas**

```python
    def sync_saga(self, saga_name: str, executive_summary: str, media_ids: List[str]):
        """
        Creates a Saga node and links it to its media items.
        """
        if not self.driver:
            return
            
        query = """
        MERGE (s:Saga {name: $saga_name})
        SET s.executive_summary = $summary
        WITH s
        UNWIND $ids as mid
        MATCH (m:Media {id: mid})
        MERGE (s)-[:CONTAINS_MEDIA]->(m)
        """
        with self.driver.session() as session:
            try:
                session.run(query, saga_name=saga_name, summary=executive_summary, ids=media_ids)
            except Exception as e:
                logger.error(f"Failed to sync saga {saga_name}: {e}")
```

- [ ] **Step 2: Commit**

```bash
git add backend/pipeline/neo4j_client.py
git commit -m "feat: add Saga sync capabilities to Neo4j client"
```

---

### Task 2: Implement Saga Ingestion Pipeline

**Files:**
- Create: `backend/pipeline/anime/6_generate_sagas.py`

- [ ] **Step 1: Implement franchise grouping and summarization**
  - Group `MediaItem` from `data/processed/clean_root_animes.json` by their `series` or `franchise` name.
  - For each group, use `LLMService` to generate a high-density `executive_summary`.
  - Call `neo4j_manager.sync_saga`.

- [ ] **Step 2: Commit**

```bash
git add backend/pipeline/anime/6_generate_sagas.py
git commit -m "feat: implement Saga ingestion and summarization pipeline"
```

---

### Task 3: Create Saga Agent

**Files:**
- Create: `backend/core/domain/services/rag/agents/saga_agent.py`

- [ ] **Step 1: Implement `SagaAgent` class**
  - Implement `lookup_saga(query)`: Finds relevant Saga in Neo4j.
  - Implement `get_saga_context(saga_name)`: Returns the executive summary.

- [ ] **Step 2: Commit**

```bash
git add backend/core/domain/services/rag/agents/saga_agent.py
git commit -m "feat: implement SagaAgent for macro-context retrieval"
```

---

### Task 4: Integrate SAGA_LOOKUP State in AgenticRAGService

**Files:**
- Modify: `backend/core/domain/services/agentic_rag_service.py`
- Modify: `backend/api/animetix/containers.py`

- [ ] **Step 1: Add `SAGA_LOOKUP` to `RAGState`**

- [ ] **Step 2: Implement `_handle_saga_lookup(self, ctx: RAGContext)`**
  - Use `SagaAgent` to find global context.
  - Injected result into `ctx.truth_path` with a `### GLOBAL SAGA CONTEXT ###` header.
  - Transition to `RESEARCH`.

- [ ] **Step 3: Update `Planner` to trigger Saga lookup**
  - Add `requires_saga: bool = False` to `SearchPlan`.
  - Route from `PLAN` to `SAGA_LOOKUP` if True.

- [ ] **Step 4: Commit**

```bash
git add backend/core/domain/services/agentic_rag_service.py backend/api/animetix/containers.py
git commit -m "feat: integrate SAGA_LOOKUP cascading state into AgenticRAG"
```

---

### Task 5: End-to-End Verification

**Files:**
- Create: `tests/core/test_world_brain_cascading.py`

- [ ] **Step 1: Write integration test for long-running series**
  - Mock a query about One Piece.
  - Verify that `SAGA_LOOKUP` is reached first.
  - Verify that the final synthesis uses both Saga and Episode context.

- [ ] **Step 2: Run test**

Run: `pytest tests/core/test_world_brain_cascading.py -v`

- [ ] **Step 3: Commit final changes**

```bash
git add .
git commit -m "docs: finalize World-Brain (Infinite Context) integration"
```
