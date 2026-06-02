# HTTPX Migration Plan - Batches 3 to 6

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate remaining files in Batches 3, 4, 5, and 6 from `requests` to `httpx`.

**Architecture:** Surgical replacement of `requests` library with `httpx`, ensuring `follow_redirects=True` is added to all request calls to maintain parity with `requests` default behavior.

**Tech Stack:** Python, httpx

---

## Batch 3: Characters Ingestion

### Task 1: Migrate `backend/pipeline/characters/extract_akinetix_attributes.py`
**Files:**
- Modify: `backend/pipeline/characters/extract_akinetix_attributes.py`

- [ ] **Step 1: Replace import and post call**
```python
import httpx # was import requests
...
response = httpx.post(f"{BRAIN_URL}/generate", json={...}, follow_redirects=True) # was requests.post
```

### Task 2: Migrate `backend/pipeline/characters/ingest_characters.py`
**Files:**
- Modify: `backend/pipeline/characters/ingest_characters.py`

- [ ] **Step 1: Replace import and post call**
```python
import httpx # was import requests
...
response = httpx.post(url, json={'query': query, 'variables': variables}, timeout=30, follow_redirects=True) # was requests.post
```

---

## Batch 4: Character Refinement & Data Intelligence

### Task 3: Migrate `backend/pipeline/characters/ingest_vg_characters.py`
**Files:**
- Modify: `backend/pipeline/characters/ingest_vg_characters.py`

- [ ] **Step 1: Replace import and post calls**
```python
import httpx # was import requests
...
res = httpx.post(url, follow_redirects=True) # was requests.post(url)
...
response = httpx.post(url, headers=headers, data=query, follow_redirects=True) # was requests.post
```

### Task 4: Migrate `backend/pipeline/characters/refine_characters.py`
**Files:**
- Modify: `backend/pipeline/characters/refine_characters.py`

- [ ] **Step 1: Replace import and post call**
```python
import httpx # was import requests
...
response = httpx.post(f"{BRAIN_URL}/generate", json={...}, follow_redirects=True) # was requests.post
```

### Task 5: Migrate `backend/pipeline/characters/vectorize_characters.py`
**Files:**
- Modify: `backend/pipeline/characters/vectorize_characters.py`

- [ ] **Step 1: Replace import and get call**
```python
import httpx # was import requests
...
res = httpx.get(item['image'], timeout=5, follow_redirects=True) # was requests.get
```

### Task 6: Migrate `backend/pipeline/data_intelligence.py`
**Files:**
- Modify: `backend/pipeline/data_intelligence.py`

- [ ] **Step 1: Replace import and post call**
```python
import httpx # was import requests
...
response = httpx.post(f"{self.brain_url}/generate", json={...}, follow_redirects=True) # was requests.post
```

### Task 7: Migrate `backend/pipeline/enrich_db_scraper.py`
**Files:**
- Modify: `backend/pipeline/enrich_db_scraper.py`

- [ ] **Step 1: Replace import and get call**
```python
import httpx # was import requests
...
response = httpx.get(url, timeout=15, follow_redirects=True) # was requests.get
```

---

## Batch 5: AI Enrichment & Evaluation

### Task 8: Migrate `backend/pipeline/enrich_graph_ai.py`
**Files:**
- Modify: `backend/pipeline/enrich_graph_ai.py`

- [ ] **Step 1: Replace import and get calls**
```python
import httpx # was import requests
...
res = httpx.get(url_full, timeout=10, follow_redirects=True)
...
res = httpx.get(url_staff, timeout=10, follow_redirects=True)
...
res = httpx.get(url_chars, timeout=10, follow_redirects=True)
```

### Task 9: Migrate `backend/pipeline/evaluation/compare_models_wandb.py`
**Files:**
- Modify: `backend/pipeline/evaluation/compare_models_wandb.py`

- [ ] **Step 1: Replace import and request calls**
```python
import httpx # was import requests
...
response = httpx.post(BRAIN_URL, json={...}, follow_redirects=True)
...
res = httpx.get("http://127.0.0.1:7860/", follow_redirects=True)
```

### Task 10: Migrate `backend/pipeline/evaluation/drift_detection.py`
**Files:**
- Modify: `backend/pipeline/evaluation/drift_detection.py`

- [ ] **Step 1: Replace import and get call**
```python
import httpx # was import requests
...
res = httpx.get("https://api.jikan.moe/v4/seasons/now", timeout=10, follow_redirects=True)
```

### Task 11: Migrate `backend/pipeline/evaluation/eval_ragas.py`
**Files:**
- Modify: `backend/pipeline/evaluation/eval_ragas.py`

- [ ] **Step 1: Replace import and post call**
```python
import httpx # was import requests
...
response = httpx.post(self.brain_url, json={...}, follow_redirects=True)
```

### Task 12: Migrate `backend/pipeline/expert_scrapers.py`
**Files:**
- Modify: `backend/pipeline/expert_scrapers.py`

- [ ] **Step 1: Replace import and get call**
```python
import httpx # was import requests
...
response = httpx.get(url, timeout=15, follow_redirects=True)
```

---

## Batch 6: Games & Manga Ingestion

### Task 13: Migrate `backend/pipeline/games/ingest_games.py`
**Files:**
- Modify: `backend/pipeline/games/ingest_games.py`

- [ ] **Step 1: Replace import and post calls**
```python
import httpx # was import requests
...
response = httpx.post(url, follow_redirects=True)
...
response = httpx.post(url, headers=headers, data=query, follow_redirects=True)
```

### Task 14: Migrate `backend/pipeline/jikan_enrichment.py`
**Files:**
- Modify: `backend/pipeline/jikan_enrichment.py`

- [ ] **Step 1: Replace import and get calls**
```python
import httpx # was import requests
...
response = httpx.get(url, timeout=15, follow_redirects=True)
...
response = httpx.get(url, timeout=15, follow_redirects=True)
```

### Task 15: Migrate `backend/pipeline/manga/fetch_covers.py`
**Files:**
- Modify: `backend/pipeline/manga/fetch_covers.py`

- [ ] **Step 1: Replace import and get calls**
```python
import httpx # was import requests
...
response = httpx.get(f"{MALSYNC_API_URL}/{mal_id}", timeout=10, follow_redirects=True)
...
response = httpx.get(f"{MANGADEX_API_URL}/cover", params=params, timeout=10, follow_redirects=True)
```

### Task 16: Migrate `backend/pipeline/manga/ingest_manga.py`
**Files:**
- Modify: `backend/pipeline/manga/ingest_manga.py`

- [ ] **Step 1: Replace import and post call**
```python
import httpx # was import requests
...
response = httpx.post(url, json={'query': query, 'variables': variables}, timeout=30, follow_redirects=True)
```

### Task 17: Migrate `backend/pipeline/manga/vectorize_manga.py`
**Files:**
- Modify: `backend/pipeline/manga/vectorize_manga.py`

- [ ] **Step 1: Replace import and get call**
```python
import httpx # was import requests
...
res = httpx.get(item['image'], timeout=2, follow_redirects=True)
```
