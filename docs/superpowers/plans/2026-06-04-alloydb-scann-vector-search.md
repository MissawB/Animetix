# AlloyDB AI & Vector Search (ScaNN) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate to AlloyDB to use ScaNN indexing and source vectorization via google_ml_integration with text-embedding-005, supporting local development and test fallbacks.

**Architecture:** Probe for `google_ml_integration` and `alloydb_scann` extensions at startup. If active, perform vectorization and query directly on the PostgreSQL/AlloyDB side using database-side SQL function calls. Otherwise, fall back to local SentenceTransformer embedding.

**Tech Stack:** Django, PostgreSQL (pgvector, alloydb_scann, google_ml_integration), SQLite, pytest.

---

### Task 1: Add configuration in settings.py

**Files:**
- Modify: [settings.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix_project/settings.py)

- [ ] **Step 1: Add ALLOYDB_EMBEDDING_MODEL setting**

Add the configuration setting at the end of [settings.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix_project/settings.py):
```python
ALLOYDB_EMBEDDING_MODEL = env('ALLOYDB_EMBEDDING_MODEL', default='text-embedding-005')
```

- [ ] **Step 2: Commit settings change**

Run:
```bash
git add backend/api/animetix_project/settings.py
git commit -m "config: add ALLOYDB_EMBEDDING_MODEL setting"
```

---

### Task 2: Create Django Database Migration

**Files:**
- Create: [0028_alloydb_scann_and_ml.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix/migrations/0028_alloydb_scann_and_ml.py)

- [ ] **Step 1: Write the migration script**

Create [0028_alloydb_scann_and_ml.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix/migrations/0028_alloydb_scann_and_ml.py):
```python
from django.db import migrations

def setup_alloydb_features(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        # Enable google_ml_integration
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS google_ml_integration CASCADE;")
        except Exception as e:
            print(f"Warning: Could not enable google_ml_integration: {e}")
            
        # Enable alloydb_scann
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS alloydb_scann CASCADE;")
        except Exception as e:
            print(f"Warning: Could not enable alloydb_scann: {e}")
            
        # Create ScaNN index on VectorRecord embedding column
        try:
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS animetix_vectorrecord_embedding_scann_idx "
                "ON animetix_vectorrecord USING scann (embedding cosine) "
                "WITH (num_leaves = 100);"
            )
        except Exception as e:
            print(f"Warning: Could not create ScaNN index: {e}")

class Migration(migrations.Migration):
    dependencies = [
        ('animetix', '0027_pgvector_migration'),
    ]
    operations = [
        migrations.RunPython(setup_alloydb_features, reverse_code=migrations.RunPython.noop),
    ]
```

- [ ] **Step 2: Run migration locally**

Run:
```bash
.venv\Scripts\python backend/api/manage.py migrate
```
Expected: Migration runs successfully under local environment (SQLite).

- [ ] **Step 3: Commit migration**

Run:
```bash
git add backend/api/animetix/migrations/0028_alloydb_scann_and_ml.py
git commit -m "db: add migration for alloydb extensions and scann index"
```

---

### Task 3: Dynamic AlloyDB AI Detection & Wrapper Updates

**Files:**
- Modify: [chroma_client.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/pipeline/chroma_client.py)
- Create: [test_alloydb_ai.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/tests/core/test_alloydb_ai.py)

- [ ] **Step 1: Update chroma_client.py with dynamic detection helper and upsert/query updates**

Modify [chroma_client.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/pipeline/chroma_client.py):
1. Add `_alloydb_ai_supported = None` and `is_alloydb_ai_supported()` at module level.
2. Update `PGVectorCollectionWrapper.upsert` to support SQL-native embedding.
3. Update `PGVectorCollectionWrapper.query` to support querying by texts.

```python
_alloydb_ai_supported = None

def is_alloydb_ai_supported():
    global _alloydb_ai_supported
    if _alloydb_ai_supported is not None:
        return _alloydb_ai_supported
        
    from django.db import connection
    if connection.vendor != 'postgresql':
        _alloydb_ai_supported = False
        return False
        
    try:
        from django.conf import settings
        model_name = getattr(settings, 'ALLOYDB_EMBEDDING_MODEL', 'text-embedding-005')
        with connection.cursor() as cursor:
            cursor.execute("SELECT embedding(%s, 'test');", [model_name])
            cursor.fetchone()
        _alloydb_ai_supported = True
        logger.info(f"[AlloyDB AI] google_ml_integration is supported with model {model_name}.")
    except Exception as e:
        _alloydb_ai_supported = False
        logger.info(f"[AlloyDB AI] google_ml_integration is not active or failed: {e}. Falling back to local embeddings.")
    return _alloydb_ai_supported
```

And update the methods in `PGVectorCollectionWrapper`:
```python
    def upsert(self, ids, embeddings=None, metadatas=None, documents=None):
        from animetix.models import VectorRecord
        from django.conf import settings
        model_name = getattr(settings, 'ALLOYDB_EMBEDDING_MODEL', 'text-embedding-005')
        
        # SOTA sanitization: convert list/dicts in metadata to strings
        clean_metas = []
        if metadatas:
            for meta in metadatas:
                clean_meta = {}
                for k, v in meta.items():
                    if isinstance(v, (list, dict)):
                        if isinstance(v, list):
                            clean_meta[k] = ", ".join([str(x) for x in v])
                        else:
                            clean_meta[k] = json.dumps(v)
                    else:
                        clean_meta[k] = v
                clean_metas.append(clean_meta)
        else:
            clean_metas = [{} for _ in ids]

        documents = documents or [None] * len(ids)
        
        if connection.vendor == 'postgresql' and is_alloydb_ai_supported():
            with transaction.atomic():
                with connection.cursor() as cursor:
                    for i, item_id in enumerate(ids):
                        doc = documents[i]
                        if doc:
                            sql = """
                                INSERT INTO animetix_vectorrecord (collection_name, item_id, embedding, metadata, document, created_at)
                                VALUES (%s, %s, embedding(%s, %s), %s, %s, NOW())
                                ON CONFLICT (collection_name, item_id)
                                DO UPDATE SET
                                    embedding = embedding(%s, EXCLUDED.document),
                                    metadata = EXCLUDED.metadata,
                                    document = EXCLUDED.document;
                            """
                            cursor.execute(sql, [self.name, str(item_id), model_name, doc, json.dumps(clean_metas[i]), doc, model_name])
                        else:
                            sql = """
                                INSERT INTO animetix_vectorrecord (collection_name, item_id, embedding, metadata, document, created_at)
                                VALUES (%s, %s, NULL, %s, NULL, NOW())
                                ON CONFLICT (collection_name, item_id)
                                DO UPDATE SET
                                    metadata = EXCLUDED.metadata;
                            """
                            cursor.execute(sql, [self.name, str(item_id), json.dumps(clean_metas[i])])
            return

        # Fallback local SQLite / standard Postgres logic
        embeddings = embeddings or [None] * len(ids)
        with transaction.atomic():
            for i, item_id in enumerate(ids):
                VectorRecord.objects.update_or_create(
                    collection_name=self.name,
                    item_id=str(item_id),
                    defaults={
                        "embedding": embeddings[i],
                        "metadata": clean_metas[i],
                        "document": documents[i],
                    }
                )
```

And update `query`:
```python
    def query(self, query_embeddings=None, query_texts=None, n_results=10, where=None, offset=0):
        from animetix.models import VectorRecord
        from django.conf import settings
        model_name = getattr(settings, 'ALLOYDB_EMBEDDING_MODEL', 'text-embedding-005')
        
        if query_embeddings is None and query_texts is None:
            return {"ids": [[]], "metadatas": [[]], "distances": [[]], "documents": [[]]}

        results_ids, results_metas, results_docs, results_distances = [], [], [], []
        use_alloydb = connection.vendor == 'postgresql' and is_alloydb_ai_supported()
        
        loop_vals = query_texts if (use_alloydb and query_texts) else (query_embeddings or [])

        for q_val in loop_vals:
            if connection.vendor == 'postgresql':
                if use_alloydb and query_texts:
                    # Native AlloyDB AI vectorization query
                    sql = """
                        SELECT item_id, metadata, document, (embedding <=> embedding(%s, %s)::vector) as distance
                        FROM animetix_vectorrecord
                        WHERE collection_name = %s
                    """
                    params = [model_name, q_val, self.name]
                    if where:
                        for k, v in where.items():
                            sql += " AND metadata @> %s"
                            params.append(json.dumps({k: v}))
                    sql += " ORDER BY embedding <=> embedding(%s, %s)::vector LIMIT %s OFFSET %s"
                    params.extend([model_name, q_val, n_results, offset])
                else:
                    # Native pgvector cosine distance query
                    sql = """
                        SELECT item_id, metadata, document, (embedding <=> %s::vector) as distance
                        FROM animetix_vectorrecord
                        WHERE collection_name = %s
                    """
                    params = [q_val, self.name]
                    if where:
                        for k, v in where.items():
                            sql += " AND metadata @> %s"
                            params.append(json.dumps({k: v}))
                    sql += " ORDER BY embedding <=> %s::vector LIMIT %s OFFSET %s"
                    params.extend([q_val, n_results, offset])

                with connection.cursor() as cursor:
                    cursor.execute(sql, params)
                    rows = cursor.fetchall()
                
                ids, metas, docs, dists = [], [], [], []
                for row in rows:
                    ids.append(row[0])
                    metas.append(row[1])
                    docs.append(row[2] or "")
                    dists.append(row[3])
                
                results_ids.append(ids)
                results_metas.append(metas)
                results_docs.append(docs)
                results_distances.append(dists)
            else:
                # SQLite fallback logic
                qs = VectorRecord.objects.filter(collection_name=self.name)
                if where:
                    for k, v in where.items():
                        qs = qs.filter(metadata__contains={k: v})

                records = list(qs)
                if not records:
                    results_ids.append([])
                    results_metas.append([])
                    results_docs.append([])
                    results_distances.append([])
                    continue

                record_embeddings = [r.embedding for r in records]
                
                # Check dimensional consistency
                clean_embeddings = []
                clean_records = []
                for idx, emb in enumerate(record_embeddings):
                    if emb is not None and len(emb) == len(q_val):
                        clean_embeddings.append(emb)
                        clean_records.append(records[idx])
                
                if not clean_embeddings:
                    results_ids.append([])
                    results_metas.append([])
                    results_docs.append([])
                    results_distances.append([])
                    continue

                q_vec_arr = np.array(q_val).reshape(1, -1)
                matrix = np.array(clean_embeddings)
                
                similarities = cosine_similarity(q_vec_arr, matrix)[0]
                distances = 1.0 - similarities
                
                sorted_indices = np.argsort(distances)[offset:offset+n_results]
                
                ids, metas, docs, dists = [], [], [], []
                for idx in sorted_indices:
                    rec = clean_records[idx]
                    ids.append(rec.item_id)
                    metas.append(rec.metadata)
                    docs.append(rec.document or "")
                    dists.append(float(distances[idx]))
                
                results_ids.append(ids)
                results_metas.append(metas)
                results_docs.append(docs)
                results_distances.append(dists)

        return {
            "ids": results_ids,
            "metadatas": results_metas,
            "documents": results_docs,
            "distances": results_distances
        }
```

- [ ] **Step 2: Create unit tests in test_alloydb_ai.py**

Create [test_alloydb_ai.py](file:///c:/Users/bahma%5CPycharmProjects%5CProjet%20solo%5CDouble_scenario_Project%5Ctests%5Ccore%5Ctest_alloydb_ai.py):
```python
import pytest
from unittest.mock import MagicMock, patch
from pipeline.chroma_client import is_alloydb_ai_supported, PGVectorCollectionWrapper

@patch('django.db.connection.vendor', 'postgresql')
def test_alloydb_ai_detection_success():
    with patch('django.db.connection.cursor') as mock_cursor:
        mock_cursor.return_value.__enter__.return_value.fetchone.return_value = ([0.1, 0.2],)
        
        import pipeline.chroma_client
        pipeline.chroma_client._alloydb_ai_supported = None
        
        assert is_alloydb_ai_supported() is True

@patch('django.db.connection.vendor', 'postgresql')
def test_alloydb_ai_detection_failure():
    with patch('django.db.connection.cursor') as mock_cursor:
        mock_cursor.return_value.__enter__.return_value.execute.side_effect = Exception("No function")
        
        import pipeline.chroma_client
        pipeline.chroma_client._alloydb_ai_supported = None
        
        assert is_alloydb_ai_supported() is False

@patch('django.db.connection.vendor', 'postgresql')
@patch('pipeline.chroma_client.is_alloydb_ai_supported', return_value=True)
def test_alloydb_ai_query_structure(mock_detect):
    wrapper = PGVectorCollectionWrapper("test_coll")
    with patch('django.db.connection.cursor') as mock_cursor:
        mock_cursor.return_value.__enter__.return_value.fetchall.return_value = []
        
        wrapper.query(query_texts=["hello"], n_results=5)
        
        calls = mock_cursor.return_value.__enter__.return_value.execute.call_args_list
        assert any("embedding(" in call[0][0] for call in calls)
```

- [ ] **Step 3: Run the new detection and query tests**

Run:
```bash
.venv\Scripts\pytest tests/core/test_alloydb_ai.py -v
```
Expected: PASS.

- [ ] **Step 4: Commit changes**

Run:
```bash
git add backend/pipeline/chroma_client.py tests/core/test_alloydb_ai.py
git commit -m "feat: integrate AlloyDB AI source vectorization in PGVectorCollectionWrapper"
```

---

### Task 4: Update Repository Ports & Adapters

**Files:**
- Modify: [repository_port.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/core/ports/repository_port.py)
- Modify: [django_repository_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/persistence/django_repository_adapter.py)
- Modify: [unified_repository_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/persistence/unified_repository_adapter.py)
- Modify: [pgvector_repository_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/persistence/pgvector_repository_adapter.py)

- [ ] **Step 1: Add documents argument to RepositoryPort.upsert_items**

Modify [repository_port.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/core/ports/repository_port.py) around line 26:
```python
    @abstractmethod
    def upsert_items(self, collection_name: str, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict], documents: Optional[List[str]] = None):
```

- [ ] **Step 2: Update DjangoRepositoryAdapter.upsert_items**

Modify [django_repository_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/persistence/django_repository_adapter.py) around line 31:
```python
    def upsert_items(self, collection_name: str, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict], documents: Optional[List[str]] = None):
```

- [ ] **Step 3: Update UnifiedRepositoryAdapter.upsert_items**

Modify [unified_repository_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/persistence/unified_repository_adapter.py) around line 52:
```python
    def upsert_items(self, collection_name: str, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict], documents: Optional[List[str]] = None):
        self.chroma.upsert_items(collection_name, ids, embeddings, metadatas, documents)
```

- [ ] **Step 4: Update PGVectorRepositoryAdapter.upsert_items**

Modify [pgvector_repository_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/persistence/pgvector_repository_adapter.py) around line 112:
```python
    def upsert_items(self, collection_name: str, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict], documents: Optional[List[str]] = None):
        try:
            coll = self.manager.get_collection(name=collection_name)
            coll.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)
        except Exception as e:
            logger.error(f"PGVector Upsert Error in {collection_name}: {e}")
```

- [ ] **Step 5: Update PGVectorRepositoryAdapter.search_media_items to utilize is_alloydb_ai_supported()**

Modify [pgvector_repository_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/persistence/pgvector_repository_adapter.py) around line 166:
```python
    def search_media_items(self, query: str, media_type: Optional[str] = None, limit: int = 10, offset: int = 0) -> List[Dict]:
        if not media_type:
            media_type = 'Anime'
            
        coll_name = self.coll_names.get(media_type)
        if not coll_name:
            return []
            
        try:
            coll = self.manager.get_collection(name=coll_name)
            
            from pipeline.chroma_client import is_alloydb_ai_supported
            if is_alloydb_ai_supported():
                res = coll.query(query_texts=[query], n_results=limit, offset=offset)
            else:
                expected_dim = 768
                test_res = coll.get(limit=1, include=['embeddings'])
                if test_res and test_res.get('embeddings') is not None and len(test_res['embeddings']) > 0:
                    expected_dim = len(test_res['embeddings'][0])
                
                query_vector = self.embedding_fn([query])[0]
                
                if len(query_vector) != expected_dim:
                    if len(query_vector) > expected_dim:
                        query_vector = query_vector[:expected_dim]
                    else:
                        query_vector = list(query_vector) + [0.0] * (expected_dim - len(query_vector))
                
                res = coll.query(query_embeddings=[query_vector], n_results=limit, offset=offset)
                
            results = []
            if res and res.get('metadatas') and res['metadatas'][0]:
                for meta, doc_id in zip(res['metadatas'][0], res['ids'][0]):
                    doc = dict(meta)
                    doc['id'] = doc_id
                    results.append(doc)
            return results
        except Exception as e:
            logger.error(f"PGVector Search Error in search_media_items for {media_type}: {e}")
            return []
```

- [ ] **Step 6: Run all vector tests to verify everything is functional**

Run:
```bash
.venv\Scripts\pytest tests/core/test_alloydb_ai.py tests/core/test_pgvector_adapter.py tests/pipeline/test_vector_client.py -v
```
Expected: PASS.

- [ ] **Step 7: Commit ports and adapters changes**

Run:
```bash
git add backend/core/ports/repository_port.py backend/adapters/persistence/django_repository_adapter.py backend/adapters/persistence/unified_repository_adapter.py backend/adapters/persistence/pgvector_repository_adapter.py
git commit -m "feat: support documents parameter and AlloyDB AI search in PGVectorRepositoryAdapter"
```
