# Gold Set Architectural Improvement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Manually add high-quality architectural queries (Graph & Visual) and update evaluation metrics to benchmark them.

**Architecture:** Enhance `gold_dataset.json` schema to include `query_type` and `ground_truth`, add ~50 expert queries across 5 categories, and update `evaluation_metrics.py` for per-category reporting in W&B.

**Tech Stack:** Python, Ragas, Neo4j, SigLIP, W&B.

---

### Task 1: Add Integrity Test for Gold Set Schema

**Files:**
- Create: `tests/mlops/test_gold_set_integrity.py`

- [ ] **Step 1: Write the failing test**

```python
import json
import os
import pytest

def test_gold_set_schema_integrity():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    gold_path = os.path.join(base_dir, 'data', 'mlops', 'gold_dataset.json')
    
    with open(gold_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for entry in data:
        # Check new mandatory fields for architectural queries
        if entry.get('is_architectural'):
            assert 'query_type' in entry
            assert 'ground_truth' in entry
            assert entry['query_type'] in ['graph', 'visual', 'thematic', 'cross-media', 'negative']
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/mlops/test_gold_set_integrity.py -v`
Expected: FAIL (assertion error because these fields don't exist yet)

- [ ] **Step 3: Commit**

```bash
git add tests/mlops/test_gold_set_integrity.py
git commit -m "test: add integrity check for gold set architectural fields"
```

---

### Task 2: Implement Architectural Queries in Gold Set

**Files:**
- Modify: `data/mlops/gold_dataset.json`

- [ ] **Step 1: Append new queries (Sample shown, total ~50)**

```json
  {
    "query": "Quels sont les autres animés produits par le studio qui a fait Attack on Titan ?",
    "expected_id": "16498",
    "expected_title": "Attack on Titan",
    "is_architectural": true,
    "query_type": "graph",
    "ground_truth": "Le studio Wit Studio a produit Attack on Titan (saisons 1-3), ainsi que Vinland Saga et Kabaneri of the Iron Fortress."
  },
  {
    "query": "L'animé avec un personnage aux cheveux argentés portant un masque et lisant un livre.",
    "expected_id": "20",
    "expected_title": "Naruto",
    "is_architectural": true,
    "query_type": "visual",
    "ground_truth": "Kakashi Hatake de Naruto correspond à cette description."
  }
```

- [ ] **Step 2: Run integrity test to verify it passes**

Run: `pytest tests/mlops/test_gold_set_integrity.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add data/mlops/gold_dataset.json
git commit -m "feat: add expert architectural queries to gold set"
```

---

### Task 3: Update Evaluation Metrics for Per-Category Reporting

**Files:**
- Modify: `backend/pipeline/mlops/evaluation_metrics.py`

- [ ] **Step 1: Update `ragas_performance_comparison` to support filtering**

```python
# ... in ragas_performance_comparison ...
    with open(GOLD_DATASET, 'r', encoding='utf-8') as f:
        gold_data = json.load(f)

    # Separate standard and architectural queries
    standard_set = [e for e in gold_data if not e.get('is_architectural')]
    arch_set = [e for e in gold_data if e.get('is_architectural')]
    
    # Official eval uses a mix
    eval_set = standard_set[:50] + arch_set[:50]
# ... update data dict to use entry.get('ground_truth', entry['expected_title']) ...
```

- [ ] **Step 2: Update W&B logging for categories**

```python
# ... inside the loop after evaluate() ...
            per_type_metrics = {}
            df = result.to_pandas()
            df['query_type'] = [e.get('query_type', 'standard') for e in eval_set]
            
            for q_type in df['query_type'].unique():
                type_avg = df[df['query_type'] == q_type].mean().to_dict()
                per_type_metrics[q_type] = type_avg
                wandb.log({f"{mode}_{q_type}_{k}": v for k, v in type_avg.items() if isinstance(v, (int, float))})
```

- [ ] **Step 3: Commit**

```bash
git add backend/pipeline/mlops/evaluation_metrics.py
git commit -m "feat: add per-category performance reporting in MLOps pipeline"
```

---

### Task 4: Final Validation with Smoke Test

**Files:**
- Run: `scripts/rag_smoke_test.py`

- [ ] **Step 1: Execute smoke test**

Run: `python scripts/rag_smoke_test.py`
Expected: Output showing successful evaluation and stable performance.

- [ ] **Step 2: Verify W&B (if possible) or check logs for category scores**

- [ ] **Step 3: Commit final changes**

```bash
git add .
git commit -m "docs: finalize gold set improvement task"
```
