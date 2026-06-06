# ToT Exploration Tree Visualization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enrich the `TreeOfThoughtsSearchService` to capture the full exploration tree (nodes and links) instead of just the best path.

**Architecture:** 
- Maintain `nodes` and `links` lists during the ToT search.
- Each thought (node) gets a unique ID: `node_{step}_{parent_idx}_{branch_idx}`.
- Relationships are captured as directed links from parent to child.
- Nodes track metadata: `label`, `full_text`, `score`, `status` ("root", "selected", "pruned", "final").

**Tech Stack:** Python, pytest, unit mocks.

---

### Task 1: Setup TDD and Initial Tree Structure

**Files:**
- Create: `tests/core/test_tot_service_tree.py`
- Modify: `backend/core/domain/services/tree_of_thoughts_service.py`

- [ ] **Step 1: Write the failing test for full_tree presence**

```python
def test_tot_returns_full_tree_structure():
    from unittest.mock import MagicMock
    from core.domain.services.tree_of_thoughts_service import TreeOfThoughtsSearchService
    
    mock_engine = MagicMock()
    mock_engine.generate.return_value = "0.8" # default score
    
    service = TreeOfThoughtsSearchService(inference_engine=mock_engine, prompt_manager=MagicMock())
    result = service.solve_with_tree_of_thoughts(query="Test query", breadth=1, depth=1)
    
    assert "full_tree" in result
    assert "nodes" in result["full_tree"]
    assert "links" in result["full_tree"]
    # Check root node
    root = result["full_tree"]["nodes"][0]
    assert root["id"] == "node_0_0"
    assert root["status"] == "root"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_tot_service_tree.py`
Expected: FAIL with `KeyError: 'full_tree'`

- [ ] **Step 3: Modify service to initialize and return empty tree**

```python
# In solve_with_tree_of_thoughts
full_tree = {
    "nodes": [{"id": "node_0_0", "label": "Start", "full_text": "Start", "score": 1.0, "status": "root"}],
    "links": []
}
# ... existing logic ...
# return { ..., "full_tree": full_tree }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/core/test_tot_service_tree.py`
Expected: PASS

---

### Task 2: Implement Node and Link Capture

- [ ] **Step 1: Update test to expect generated nodes and links**

```python
def test_tot_captures_generated_nodes():
    from unittest.mock import MagicMock
    from core.domain.services.tree_of_thoughts_service import TreeOfThoughtsSearchService
    
    mock_engine = MagicMock()
    # 1 thought, 1 score, 1 synthesis
    mock_engine.generate.side_effect = ["Thought 1", "0.9", "Final Answer"]
    
    service = TreeOfThoughtsSearchService(inference_engine=mock_engine, prompt_manager=MagicMock())
    result = service.solve_with_tree_of_thoughts(query="Test", breadth=1, depth=1)
    
    nodes = result["full_tree"]["nodes"]
    links = result["full_tree"]["links"]
    
    assert len(nodes) == 2  # Root + 1 thought
    assert any(n["id"] == "node_1_0_0" for n in nodes)
    assert len(links) == 1
    assert links[0]["source"] == "node_0_0"
    assert links[0]["target"] == "node_1_0_0"
```

- [ ] **Step 2: Implement capture logic in the service loop**

- [ ] **Step 3: Verify tests pass**

---

### Task 3: Implement Status Logic (Pruned/Selected/Final)

- [ ] **Step 1: Update test for status transitions**

```python
def test_tot_node_statuses():
    # Mock engine to return one high score and one low score
    # Verify that the low score node has status="pruned"
    # Verify that the best path nodes have status="final"
```

- [ ] **Step 2: Implement status marking logic**

- [ ] **Step 3: Verify tests pass**

---

### Task 4: Final Verification and Commit

- [ ] **Step 1: Run all tests including legacy tests**
- [ ] **Step 2: Commit changes**
