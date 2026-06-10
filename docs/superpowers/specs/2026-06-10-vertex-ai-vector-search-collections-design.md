# Vertex AI Vector Search 2.0 (Collections) Design Spec

This design document outlines the integration of Vertex AI Vector Search 2.0 (Collections) into Animetix to simplify the Retrieval-Augmented Generation (RAG) architecture and enable native, GCP-managed hybrid search (dense + sparse) with Reciprocal Rank Fusion (RRF). It maintains full compatibility with the existing pgvector/SQLite dynamic fallback setup.

## User Review Required

> [!IMPORTANT]
> The dynamic fallback will switch to local CPU/GPU `SentenceTransformer` embeddings and SQLite/Postgres `VectorRecord` table during local development and testing. Production will require valid Application Default Credentials (ADC) and the `google-cloud-aiplatform` (or `google-cloud-vectorsearch`) package.

> [!NOTE]
> This migration leverages Google Cloud's **auto-embeddings** feature on collections, eliminating the need to compute embeddings locally before inserting into the cloud vector database.

## Proposed Changes

---

### Backend Config & Environment

#### [MODIFY] [settings.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix/settings.py)
*   Define settings for Vertex AI Vector Search:
    ```python
    VERTEX_AI_VECTOR_SEARCH_ACTIVE = env.bool('VERTEX_AI_VECTOR_SEARCH_ACTIVE', default=False)
    VERTEX_AI_PROJECT_ID = env('VERTEX_AI_PROJECT_ID', default='')
    VERTEX_AI_LOCATION = env('VERTEX_AI_LOCATION', default='europe-west1')
    VERTEX_AI_COLLECTION_NAME = env('VERTEX_AI_COLLECTION_NAME', default='animetix_media')
    VERTEX_AI_AUTO_EMBEDDINGS = env.bool('VERTEX_AI_AUTO_EMBEDDINGS', default=True)
    VERTEX_AI_EMBEDDING_MODEL = env('VERTEX_AI_EMBEDDING_MODEL', default='text-embedding-005')
    ```

---

### Persistence & Adapters

#### [MODIFY] [chroma_client.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/pipeline/chroma_client.py)
*   Implement `is_vertex_ai_supported()` which checks if `VERTEX_AI_VECTOR_SEARCH_ACTIVE` is True and attempts a lazy-loaded import of `google.cloud.aiplatform`.
*   Implement `VertexAICollectionWrapper` to handle `add()`, `upsert()`, `query()`, and `get()` using Vertex AI Vector Search 2.0 Collections SDK.
*   Update `PGVectorManager.get_collection()` to return `VertexAICollectionWrapper` if `is_vertex_ai_supported()` is True, otherwise fall back to `PGVectorCollectionWrapper`.

#### [MODIFY] [pgvector_repository_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/persistence/pgvector_repository_adapter.py)
*   Ensure that all repository-level queries route seamlessly through `chroma_manager` interface without being affected by the underlying collection type.

---

### Dependencies

#### [MODIFY] [requirements.txt](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/requirements.txt)
*   Add `google-cloud-aiplatform` (or `google-cloud-vectorsearch` as required by the 2.0 SDK).

---

### Automated Tests

#### [NEW] [test_vertex_ai_vector_search.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/tests/core/test_vertex_ai_vector_search.py)
*   Create a unit test suite to assert:
    *   Dynamic detection logic works.
    *   Fallback mode functions correctly on local SQLite/pgvector when Vertex AI is disabled.
    *   Calls to the wrapper correctly trigger mock SDK calls when enabled.

## Verification Plan

### Automated Tests
Run the test suite:
```bash
.venv\Scripts\pytest tests/core/test_vertex_ai_vector_search.py -v
```

### Manual Verification
1. Activate `VERTEX_AI_VECTOR_SEARCH_ACTIVE=True` in a staging environment.
2. Run `sync_catalog` management command and verify objects are created in the Vertex AI Collection.
3. Perform a semantic search query and inspect the logs to verify hybrid search and RRF are executed on the Vertex AI side.
