# Requests to HTTPX Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Standardize HTTP client usage by migrating from `requests` to `httpx` (sync) across the entire backend.

**Architecture:** Surgical replacement of `requests` calls with `httpx` equivalents, ensuring `follow_redirects=True` is set for parity with `requests` default behavior, and updating exception handling from `requests.exceptions.RequestException` to `httpx.RequestError`.

**Tech Stack:** Python, `httpx`.

---

### Task 1: Core Inference Adapters

**Files:**
- Modify: `backend/adapters/inference/brain_api_adapter.py`
- Modify: `backend/adapters/inference/local_rerank_adapter.py`
- Modify: `backend/adapters/inference/unified_inference_adapter.py`

- [ ] **Step 1: Migrate BrainAPIAdapter**
    - Replace `import requests` with `import httpx`.
    - Replace `requests.post(...)` with `httpx.post(..., follow_redirects=True)`.
    - Replace `requests.get(...)` with `httpx.get(..., follow_redirects=True)`.
    - Replace `requests.exceptions.RequestException` with `httpx.RequestError`.
- [ ] **Step 2: Migrate LocalRerankAdapter**
    - Apply same patterns as Step 1.
- [ ] **Step 3: Migrate UnifiedInferenceAdapter**
    - Apply same patterns as Step 1.
- [ ] **Step 4: Commit**
    - `git commit -m "refactor: migrate core inference adapters from requests to httpx"`

### Task 2: Core Persistence Adapters

**Files:**
- Modify: `backend/adapters/persistence/fandom_adapter.py`
- Modify: `backend/adapters/persistence/pipeline_sync_adapter.py`
- Modify: `backend/adapters/persistence/web_search_adapter.py`

- [ ] **Step 1: Migrate FandomAdapter**
    - Apply same patterns as Task 1.
- [ ] **Step 2: Migrate PipelineSyncAdapter**
    - Apply same patterns as Task 1.
- [ ] **Step 3: Migrate WebSearchAdapter**
    - Apply same patterns as Task 1.
- [ ] **Step 4: Commit**
    - `git commit -m "refactor: migrate core persistence adapters from requests to httpx"`

### Task 3: API Endpoints

**Files:**
- Modify: `backend/api/animetix/api/core.py`
- Modify: `backend/api/animetix/api/labs.py`

- [ ] **Step 1: Migrate animetix/api/core.py**
    - Apply same patterns as Task 1.
- [ ] **Step 2: Migrate animetix/api/labs.py**
    - Apply same patterns as Task 1.
- [ ] **Step 3: Commit**
    - `git commit -m "refactor: migrate API endpoints from requests to httpx"`

### Task 4: Domain Services & Agents

**Files:**
- Modify: `backend/core/domain/services/advanced_vision_service.py`
- Modify: `backend/core/domain/services/rag/agents/librarian.py`

- [ ] **Step 1: Migrate AdvancedVisionService**
- [ ] **Step 2: Migrate Librarian Agent**
- [ ] **Step 3: Commit**
    - `git commit -m "refactor: migrate domain services and agents from requests to httpx"`

### Task 5: Pipeline Logic (Core)

**Files:**
- Modify: `backend/pipeline/actors/ingest_actors.py`
- Modify: `backend/pipeline/data_intelligence.py`
- Modify: `backend/pipeline/enrich_db_scraper.py`
- Modify: `backend/pipeline/enrich_graph_ai.py`
- Modify: `backend/pipeline/expert_scrapers.py`
- Modify: `backend/pipeline/specialized_scrapers.py`
- Modify: `backend/pipeline/jikan_enrichment.py`

- [ ] **Step 1: Migrate Pipeline Core Files**
    - Process all files listed in Task 5 sequentially.
- [ ] **Step 2: Commit**
    - `git commit -m "refactor: migrate core pipeline logic from requests to httpx"`

### Task 6: Specialized Scrapers & Scripts

**Files:**
- Modify: `backend/pipeline/advanced_scrapers.py`
- Modify: `scripts/ddg_test.py`

- [ ] **Step 1: Migrate Advanced Scrapers**
- [ ] **Step 2: Migrate DDG Test Script**
- [ ] **Step 3: Commit**
    - `git commit -m "refactor: migrate specialized scrapers from requests to httpx"`

### Task 7: Anime Pipeline

**Files:**
- Modify: `backend/pipeline/anime/fetch_themes.py`
- Modify: `backend/pipeline/anime/ingest_anime.py`
- Modify: `backend/pipeline/anime/reconcile_drift.py`
- Modify: `backend/pipeline/anime/vectorize_anime.py`

- [ ] **Step 1: Migrate Anime Pipeline Files**
- [ ] **Step 2: Commit**
    - `git commit -m "refactor: migrate anime pipeline from requests to httpx"`

### Task 8: Character Pipeline

**Files:**
- Modify: `backend/pipeline/characters/extract_akinetix_attributes.py`
- Modify: `backend/pipeline/characters/ingest_characters.py`
- Modify: `backend/pipeline/characters/ingest_vg_characters.py`
- Modify: `backend/pipeline/characters/refine_characters.py`
- Modify: `backend/pipeline/characters/vectorize_characters.py`

- [ ] **Step 1: Migrate Character Pipeline Files**
- [ ] **Step 2: Commit**
    - `git commit -m "refactor: migrate character pipeline from requests to httpx"`

### Task 9: Manga, Games & Movies Pipelines

**Files:**
- Modify: `backend/pipeline/games/ingest_games.py`
- Modify: `backend/pipeline/manga/fetch_covers.py`
- Modify: `backend/pipeline/manga/ingest_manga.py`
- Modify: `backend/pipeline/manga/vectorize_manga.py`
- Modify: `backend/pipeline/movies/1_ingest_movies.py`

- [ ] **Step 1: Migrate Manga, Games & Movies Pipeline Files**
- [ ] **Step 2: Commit**
    - `git commit -m "refactor: migrate manga, games and movies pipelines from requests to httpx"`

### Task 10: MLOps & Evaluation

**Files:**
- Modify: `backend/pipeline/evaluation/compare_models_wandb.py`
- Modify: `backend/pipeline/evaluation/drift_detection.py`
- Modify: `backend/pipeline/evaluation/eval_ragas.py`
- Modify: `backend/pipeline/mlops/evaluation_metrics.py`
- Modify: `backend/pipeline/mlops/rlhf_pipeline.py`

- [ ] **Step 1: Migrate MLOps and Evaluation Files**
- [ ] **Step 2: Commit**
    - `git commit -m "refactor: migrate MLOps and evaluation files from requests to httpx"`

### Task 11: Seeder Scripts

**Files:**
- Modify: `backend/scripts/seed_face_embeddings.py`

- [ ] **Step 1: Migrate Seeder Script**
- [ ] **Step 2: Commit**
    - `git commit -m "refactor: migrate seeder script from requests to httpx"`
