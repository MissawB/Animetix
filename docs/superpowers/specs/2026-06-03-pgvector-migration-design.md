# ChromaDB to pgvector Migration Design

This design document outlines the transition of the Double_scenario_Project vector storage layer from ChromaDB to pgvector on PostgreSQL (managed by Google Cloud SQL in production). 

## Overview & Goal
Moving the vector database to PostgreSQL via pgvector ensures that the application is fully serverless-ready (stateless) and simplifies deployment, backups, and infrastructure costs by eliminating the separate ChromaDB container.

## Architecture
The system employs a **hybrid vector database approach**:
1. **Production (PostgreSQL):** Uses the `pgvector` database extension natively, executing vector similarity queries (cosine distance `<=>`) on the PostgreSQL database server.
2. **Local/Tests (SQLite):** Falls back to storing embeddings as JSON string representation in standard text columns. Vector similarity calculations are performed in memory using Python/Numpy.

---

## Proposed Changes

### 1. Database Model & Custom Field
*   **File:** [models.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix/models.py)
*   **PGVectorField:** A custom Django field that resolves to the `vector` SQL type on PostgreSQL connections and the `text` SQL type on other engines (like SQLite). It handles formatting arrays to/from vector string representation.
*   **VectorRecord Model:** Represents a generic collection table for embeddings:
    *   `collection_name` (CharField, indexed)
    *   `item_id` (CharField, indexed)
    *   `embedding` (PGVectorField)
    *   `metadata` (JSONField)
    *   `document` (TextField, optional)
    *   *Constraints:* Unique together (`collection_name`, `item_id`).

### 2. Django Migration
*   **File:** New migration `backend/api/animetix/migrations/0027_pgvector_migration.py`
*   Executes `CREATE EXTENSION IF NOT EXISTS vector;` on PostgreSQL connection before creating the `VectorRecord` table.

### 3. Pipeline Vector Client Wrapper
*   **File:** [chroma_client.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/pipeline/chroma_client.py)
*   Replaces `ChromaManager` with a `PGVectorManager` class that returns `PGVectorCollectionWrapper` instances.
*   Implements ChromaDB-compatible methods (`add`, `upsert`, `get`, `query`, `count`, `delete_collection`, `get_all_ids`) to keep data ingestion pipelines functional without modifying their code.
*   Translates Chroma query operations into raw SQL `<=>` cosine distance queries on PostgreSQL, and into Numpy similarity rankings on SQLite.

### 4. Repository Adapter
*   **File Rename:** `backend/adapters/persistence/chroma_repository_adapter.py` -> [pgvector_repository_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/persistence/pgvector_repository_adapter.py)
*   Implements the `RepositoryPort` interface using Django's connection cursor and `VectorRecord` model.
*   Performs database-side nearest-neighbor operations on PostgreSQL and Numpy-side rankings on SQLite.

### 5. Unified Repository Integration
*   **File:** [unified_repository_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/persistence/unified_repository_adapter.py)
*   Imports and wires `PGVectorRepositoryAdapter` instead of `ChromaRepositoryAdapter`.

### 6. Dependencies & Infrastructure
*   **File:** [requirements.txt](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/requirements.txt) - Removes `chromadb==1.5.5`.
*   **File:** [docker-compose.yml](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/deploy/docker-compose.yml) - Replaces `postgres:16-alpine` with `pgvector/pgvector:pg16` for local dev pgvector support, and deletes the `chromadb` service configuration completely.

---

## Verification Plan

### Automated Tests
*   **File Rename:** `tests/core/test_chroma_adapter.py` -> `tests/core/test_pgvector_adapter.py`
*   Verify that `test_pgvector_adapter.py` and `test_long_term_memory_service.py` pass successfully under SQLite in-memory configuration.
*   Command: `.venv\Scripts\pytest tests/core/test_pgvector_adapter.py tests/core/test_long_term_memory_service.py -v`
