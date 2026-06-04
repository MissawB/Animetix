# AlloyDB AI & Vector Search (ScaNN) Design Spec

This design document outlines the integration of AlloyDB AI source vectorization and ScaNN vector indexing into the application, maintaining full compatibility with the existing pgvector/SQLite dynamic persistence setup.

## Overview & Goal
Migrate database vector operations to leverage AlloyDB's `google_ml_integration` and `alloydb_scann` extensions. This allows performing vectorization directly on the database side (using `text-embedding-005` in production) and accelerates vector searches up to 100x using ScaNN indexes.

## User Review Required
No breaking changes or manual database steps are required; all database settings and extensions will be set up automatically or fall back gracefully.

## Architecture

We employ a **runtime hybrid adapter approach**:
1. **Production (AlloyDB):** Auto-detected at startup. Utilizes SQL-native `embedding()` calls for document insertions (upsert) and text query parameters (query). Performs similarity searches using a ScaNN index for high-speed retrieval.
2. **Fallback Mode (Local dev/SQLite):** Falls back to standard Python-side vectorization (`SentenceTransformerEmbeddingFunction`) and standard SQL operations, ensuring the development and testing suite remains fully functional without a local AlloyDB instance.

---

## Proposed Changes

### 1. Settings Configuration
*   **File:** [settings.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix_project/settings.py)
*   Add configuration for the embedding model to be used by AlloyDB AI:
    ```python
    ALLOYDB_EMBEDDING_MODEL = env('ALLOYDB_EMBEDDING_MODEL', default='text-embedding-005')
    ```

### 2. Django Database Migration
*   **File:** [0028_alloydb_scann_and_ml.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix/migrations/0028_alloydb_scann_and_ml.py)
*   Create a schema migration that:
    1. Enables the `google_ml_integration` extension.
    2. Enables the `alloydb_scann` extension.
    3. Creates a ScaNN index on the `VectorRecord` table's `embedding` column using cosine distance and `num_leaves = 100`.
*   All operations are wrapped in safe PostgreSQL check gates and try-except blocks to prevent crashes on SQLite/standard Postgres environments.

### 3. Dynamic AlloyDB AI Detection & Wrapper Updates
*   **File:** [chroma_client.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/pipeline/chroma_client.py)
*   Implement `is_alloydb_ai_supported()` which caches the detection state after executing a trial `SELECT embedding(...)` query on PostgreSQL.
*   Update `PGVectorCollectionWrapper.upsert()`:
    *   If AlloyDB AI is active and text documents are provided, execute a raw SQL `INSERT ... ON CONFLICT DO UPDATE` query that generates embeddings directly in PostgreSQL using `embedding(%s, EXCLUDED.document)`.
    *   Otherwise, fall back to the existing Python-side vectorized update/create logic.
*   Update `PGVectorCollectionWrapper.query()`:
    *   If AlloyDB AI is active and `query_texts` are provided, query directly using SQL-native cosine similarity against `embedding(%s, %s)::vector` instead of passing pre-computed float arrays.

### 4. Persistence Repository Adapter Updates
*   **File:** [repository_port.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/core/ports/repository_port.py)
*   **File:** [django_repository_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/persistence/django_repository_adapter.py)
*   **File:** [unified_repository_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/persistence/unified_repository_adapter.py)
*   **File:** [pgvector_repository_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/persistence/pgvector_repository_adapter.py)
*   Add optional `documents` argument to `RepositoryPort.upsert_items` and forward it in the adapters.
*   Modify `PGVectorRepositoryAdapter.search_media_items`:
    *   If `is_alloydb_ai_supported()` is true, search by calling `coll.query(query_texts=[query])` directly, avoiding local CPU/GPU-based tokenization.

---

## Verification Plan

### Automated Tests
*   Create a new unit test suite [test_alloydb_ai.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/tests/core/test_alloydb_ai.py) to assert:
    *   Dynamic detection succeeds when PostgreSQL supports the embedding extension and fails cleanly otherwise.
    *   The wrapper correctly emits queries with database-side `embedding(...)` when AlloyDB is active.
*   Run the suite using pytest:
    ```bash
    .venv\Scripts\pytest tests/core/test_alloydb_ai.py tests/core/test_pgvector_adapter.py -v
    ```
