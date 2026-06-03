# pgvector (Cloud SQL) Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the vector database storage from ChromaDB to pgvector on PostgreSQL (Cloud SQL) with SQLite in-memory fallback for local development and testing.

**Architecture:** We will implement a custom Django field `PGVectorField` that creates a native `vector` type in PostgreSQL and a `text` type in SQLite. We will build a compatible client wrapper `PGVectorManager` that replaces ChromaDB's client interface so that the data pipelines and repository adapters can execute vector operations transparently on the Django database.

**Tech Stack:** Django, PostgreSQL (pgvector), SQLite, NumPy, Pytest

---

### Task 1: Django Model & Custom Field

**Files:**
- Modify: [models.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix/models.py)
- Create: [test_pgvector_field.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/tests/core/test_pgvector_field.py)

- [ ] **Step 1: Write the failing test**

Create the file `tests/core/test_pgvector_field.py` with the following content to test the custom field serialization:

```python
import pytest
from animetix.models import PGVectorField

def test_pgvector_field_serialization():
    field = PGVectorField()
    # Test to_python/from_db_value parsing
    assert field.to_python("[0.1, 0.2, 0.3]") == [0.1, 0.2, 0.3]
    assert field.from_db_value("[0.5, 0.6]", None, None) == [0.5, 0.6]
    
    # Test get_prep_value formatting (which converts list to string representation)
    assert field.get_prep_value([0.1, 0.2]) == "[0.1,0.2]"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\pytest tests/core/test_pgvector_field.py -v`
Expected: Fail with `ImportError: cannot import name 'PGVectorField'`

- [ ] **Step 3: Write minimal implementation**

Append the custom field and model to the end of `backend/api/animetix/models.py`:

```python
import json

class PGVectorField(models.Field):
    description = "Vector representation compatible with pgvector (PostgreSQL) and JSON strings (SQLite)"

    def db_type(self, connection):
        if connection.vendor == 'postgresql':
            return 'vector'
        return 'text'

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    def to_python(self, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    def get_prep_value(self, value):
        if value is None:
            return value
        if isinstance(value, list):
            return "[" + ",".join(map(str, value)) + "]"
        return value

class VectorRecord(models.Model):
    collection_name = models.CharField(max_length=100, db_index=True)
    item_id = models.CharField(max_length=100, db_index=True)
    embedding = PGVectorField()
    metadata = models.JSONField(default=dict, blank=True)
    document = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('collection_name', 'item_id')
        indexes = [
            models.Index(fields=['collection_name', 'item_id']),
        ]

    def __str__(self):
        return f"{self.collection_name} - {self.item_id}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\pytest tests/core/test_pgvector_field.py -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add backend/api/animetix/models.py tests/core/test_pgvector_field.py
git commit -m "feat: add PGVectorField and VectorRecord model"
```

---

### Task 2: Database Migration

**Files:**
- Create: `backend/api/animetix/migrations/0027_pgvector_migration.py`

- [ ] **Step 1: Write the migration**

Create `backend/api/animetix/migrations/0027_pgvector_migration.py`:

```python
from django.db import migrations, models
import animetix.models

def enable_vector_extension(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

class Migration(migrations.Migration):

    dependencies = [
        ('animetix', '0026_delete_donation_table'),
    ]

    operations = [
        migrations.RunPython(enable_vector_extension, reverse_code=migrations.RunPython.noop),
        migrations.CreateModel(
            name='VectorRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('collection_name', models.CharField(db_index=True, max_length=100)),
                ('item_id', models.CharField(db_index=True, max_length=100)),
                ('embedding', animetix.models.PGVectorField()),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('document', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['collection_name', 'item_id'], name='animetix_ve_collect_20560a_idx')
                ],
                'unique_together': {('collection_name', 'item_id')},
            },
        ),
    ]
```

- [ ] **Step 2: Run the migrations to verify SQLite correctness**

Run: `python backend/api/manage.py migrate --settings=animetix_project.test_settings`
Expected: Migrations apply cleanly to SQLite in-memory/test environment.

- [ ] **Step 3: Commit changes**

```bash
git add backend/api/animetix/migrations/0027_pgvector_migration.py
git commit -m "feat: add pgvector schema migration"
```

---

### Task 3: Client Wrapper in `chroma_client.py`

**Files:**
- Modify: [chroma_client.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/pipeline/chroma_client.py)
- Create: [test_vector_client.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/tests/pipeline/test_vector_client.py)

- [ ] **Step 1: Write the failing test**

Create `tests/pipeline/test_vector_client.py`:

```python
import pytest
from pipeline.chroma_client import chroma_manager

@pytest.mark.django_db
def test_compatibility_vector_client():
    collection_name = "test_coll_client"
    
    # 1. Clean collection
    chroma_manager.delete_collection(collection_name)
    
    # 2. Get collection
    coll = chroma_manager.get_collection(collection_name)
    assert coll.count() == 0
    
    # 3. Add items
    ids = ["1", "2"]
    embeddings = [[1.0, 0.0], [0.0, 1.0]]
    metadatas = [{"tag": "action"}, {"tag": "comedy"}]
    coll.add(ids=ids, embeddings=embeddings, metadatas=metadatas)
    
    assert coll.count() == 2
    
    # 4. Get items
    res_get = coll.get(ids=["1"], include=["embeddings", "metadatas"])
    assert "1" in res_get["ids"]
    assert res_get["embeddings"][0] == [1.0, 0.0]
    
    # 5. Query items
    res_query = coll.query(query_embeddings=[[1.0, 0.1]], n_results=1)
    assert res_query["ids"][0][0] == "1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\pytest tests/pipeline/test_vector_client.py -v`
Expected: Fail (since `chroma_manager` is still using the old ChromaDB HTTP/Persistent Client).

- [ ] **Step 3: Implement client wrapper**

Replace the entire content of `backend/pipeline/chroma_client.py` with:

```python
import logging
import datetime
from django.db import connection, transaction
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger("animetix." + __name__)

class PGVectorCollectionWrapper:
    def __init__(self, name):
        self.name = name

    def count(self):
        from animetix.models import VectorRecord
        return VectorRecord.objects.filter(collection_name=self.name).count()

    def get(self, ids=None, limit=None, offset=None, include=None, where=None):
        from animetix.models import VectorRecord
        qs = VectorRecord.objects.filter(collection_name=self.name)
        if ids:
            qs = qs.filter(item_id__in=[str(x) for x in ids])
        if where:
            # Simple metadata filter support (e.g. user_id: X)
            for k, v in where.items():
                qs = qs.filter(metadata__contains={k: v})
                
        if offset is not None:
            qs = qs[offset:]
        if limit is not None:
            qs = qs[:limit]

        ids_list, embeddings_list, metadatas_list, documents_list = [], [], [], []
        include = include or []

        for record in qs:
            ids_list.append(record.item_id)
            if "embeddings" in include:
                embeddings_list.append(record.embedding)
            if "metadatas" in include:
                metadatas_list.append(record.metadata)
            if "documents" in include:
                documents_list.append(record.document or "")

        res = {"ids": ids_list}
        if "embeddings" in include:
            res["embeddings"] = embeddings_list
        if "metadatas" in include:
            res["metadatas"] = metadatas_list
        if "documents" in include:
            res["documents"] = documents_list
        return res

    def add(self, ids, embeddings=None, metadatas=None, documents=None):
        self.upsert(ids, embeddings, metadatas, documents)

    def upsert(self, ids, embeddings=None, metadatas=None, documents=None):
        from animetix.models import VectorRecord
        
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

    def query(self, query_embeddings=None, query_texts=None, n_results=10, where=None, offset=0):
        from animetix.models import VectorRecord
        
        # Handle simple string embeddings fallback if embedding function is missing
        if query_embeddings is None:
            return {"ids": [[]], "metadatas": [[]], "distances": [[]], "documents": [[]]}

        results_ids, results_metas, results_docs, results_distances = [], [], [], []

        for q_vec in query_embeddings:
            if connection.vendor == 'postgresql':
                # Native pgvector cosine distance query
                # <=> operator is Cosine Distance. Score is 1 - Cosine Distance.
                sql = """
                    SELECT item_id, metadata, document, (embedding <=> %s::vector) as distance
                    FROM animetix_vectorrecord
                    WHERE collection_name = %s
                """
                params = [q_vec, self.name]
                if where:
                    # Simple where constraint mapping to JSONB contains
                    for k, v in where.items():
                        sql += " AND metadata @> %s"
                        params.append(json.dumps({k: v}))
                sql += " ORDER BY embedding <=> %s::vector LIMIT %s OFFSET %s"
                params.extend([q_vec, n_results, offset])

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
                # SQLite fallback: calculate similarity in Python
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
                    if emb is not None and len(emb) == len(q_vec):
                        clean_embeddings.append(emb)
                        clean_records.append(records[idx])
                
                if not clean_embeddings:
                    results_ids.append([])
                    results_metas.append([])
                    results_docs.append([])
                    results_distances.append([])
                    continue

                q_vec_arr = np.array(q_vec).reshape(1, -1)
                matrix = np.array(clean_embeddings)
                
                similarities = cosine_similarity(q_vec_arr, matrix)[0]
                # Distance = 1 - similarity
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

class PGVectorManager:
    def __init__(self):
        logger.info("[PGVector] Using unified relational pgvector adapter.")

    def get_collection(self, name):
        return PGVectorCollectionWrapper(name)

    def get_all_ids(self, collection_name):
        collection = self.get_collection(collection_name)
        all_ids = set()
        limit = 10000
        offset = 0
        while True:
            results = collection.get(limit=limit, offset=offset)
            batch_ids = results.get('ids', [])
            if not batch_ids:
                break
            all_ids.update(batch_ids)
            offset += limit
        return all_ids

    def add_to_collection(self, collection_name, ids, embeddings, metadatas):
        collection = self.get_collection(collection_name)
        collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)

    def query_collection(self, collection_name, query_texts=None, query_embeddings=None, n_results=10):
        collection = self.get_collection(collection_name)
        return collection.query(query_embeddings=query_embeddings, n_results=n_results)

    def delete_collection(self, collection_name):
        from animetix.models import VectorRecord
        VectorRecord.objects.filter(collection_name=collection_name).delete()

    def heartbeat(self):
        return int(datetime.datetime.now().timestamp())

chroma_manager = PGVectorManager()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\pytest tests/pipeline/test_vector_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add backend/pipeline/chroma_client.py tests/pipeline/test_vector_client.py
git commit -m "feat: implement pgvector manager client compatibility wrapper"
```

---

### Task 4: Repository Adapter Implementation

**Files:**
- Create: [pgvector_repository_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/persistence/pgvector_repository_adapter.py)
- Create: [test_pgvector_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/tests/core/test_pgvector_adapter.py)
- Delete: `backend/adapters/persistence/chroma_repository_adapter.py`
- Delete: `tests/core/test_chroma_adapter.py`

- [ ] **Step 1: Write the failing test**

Create `tests/core/test_pgvector_adapter.py`:

```python
import pytest
from unittest.mock import MagicMock
from adapters.persistence.pgvector_repository_adapter import PGVectorRepositoryAdapter

@pytest.mark.django_db
def test_pgvector_repository_adapter_operations():
    adapter = PGVectorRepositoryAdapter(project_root="")
    collection_name = "test_coll_repo"
    
    # Clean and insert test data
    adapter.delete_collection(collection_name)
    adapter.upsert_items(
        collection_name=collection_name,
        ids=["1", "2"],
        embeddings=[[1.0, 0.0], [0.0, 1.0]],
        metadatas=[{"title": "Anime A"}, {"title": "Anime B"}]
    )
    
    assert adapter.get_collection_count(collection_name) == 2
    assert adapter.get_all_ids(collection_name) == ["1", "2"]
    
    # Calculate similarity (SQLite Numpy mode)
    score = adapter.calculate_similarity(collection_name, "1", "2")
    assert score == pytest.approx(0.0)
    
    # Search Nearest Neighbors
    neighbors = adapter.get_nearest_neighbors(collection_name, "1", n_results=1)
    assert neighbors["ids"][0][0] == "1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\pytest tests/core/test_pgvector_adapter.py -v`
Expected: Fail with `ModuleNotFoundError: No module named 'adapters.persistence.pgvector_repository_adapter'`

- [ ] **Step 3: Write minimal implementation**

Create `backend/adapters/persistence/pgvector_repository_adapter.py` by implementing `RepositoryPort` with dynamic PostgreSQL/SQLite engine handling:

```python
import os
import orjson
import numpy as np
import logging
from typing import Optional, Dict, List
from core.ports.repository_port import RepositoryPort
from pipeline.chroma_client import chroma_manager
from django.core.cache import cache

logger = logging.getLogger('animetix')

class PGVectorRepositoryAdapter(RepositoryPort):
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.manager = chroma_manager
        self._embedding_fn = None
        
        self.db_files = {
            'Anime': 'data/processed/clean_root_animes.json', 
            'Manga': 'data/processed/clean_root_mangas.json', 
            'Character': 'data/processed/filtered_characters.json',
            'Movie': 'data/processed/clean_root_movies.json',
            'Game': 'data/processed/clean_root_games.json',
            'Actor': 'data/processed/clean_root_actors.json'
        }
        self.coll_names = {
            'Anime': 'anime_thematic', 
            'Manga': 'manga_thematic', 
            'Character': 'character_vibe',
            'Movie': 'movie_thematic',
            'Game': 'game_thematic',
            'Actor': 'actor_vibe'
        }
        self._catalog_cache: Dict[str, Dict] = {}

    @property
    def embedding_fn(self):
        if self._embedding_fn is None:
            from chromadb.utils import embedding_functions
            self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="jinaai/jina-embeddings-v3",
                trust_remote_code=True
            )
        return self._embedding_fn

    def get_nearest_neighbors(self, collection_name: str, item_id: str, n_results: int = 5) -> Optional[Dict]:
        try:
            coll = self.manager.get_collection(name=collection_name)
            item_data = coll.get(ids=[str(item_id)], include=['embeddings'])
            embeddings = item_data.get('embeddings')
            if not embeddings:
                return None
            return coll.query(query_embeddings=embeddings, n_results=n_results)
        except Exception as e:
            logger.error(f"PGVector Error in get_nearest_neighbors: {e}")
            return None

    def calculate_similarity(self, collection_name: str, item_a_id: str, item_b_id: str) -> float:
        cache_key = f"sim_{collection_name}_{min(item_a_id, item_b_id)}_{max(item_a_id, item_b_id)}"
        cached_val = cache.get(cache_key)
        if cached_val is not None:
            return float(cached_val)
            
        try:
            coll = self.manager.get_collection(name=collection_name)
            res = coll.get(ids=[str(item_a_id), str(item_b_id)], include=['embeddings'])
            if len(res.get('embeddings', [])) == 2:
                # Slicing Matryoshka
                from sklearn.metrics.pairwise import cosine_similarity
                vec1 = np.array(res['embeddings'][0])[:256].reshape(1, -1)
                vec2 = np.array(res['embeddings'][1])[:256].reshape(1, -1)
                score = float(cosine_similarity(vec1, vec2)[0][0])
                cache.set(cache_key, score, timeout=3600*24*7)
                return score
        except Exception as e:
            logger.error(f"PGVector Similarity Error between {item_a_id} and {item_b_id}: {e}")
        return 0.0

    def load_catalog(self, media_type: str) -> Optional[Dict]:
        if media_type not in self.db_files:
            return None
            
        if media_type in self._catalog_cache:
            return self._catalog_cache[media_type]

        try:
            db_path = os.path.join(self.project_root, self.db_files[media_type])
            with open(db_path, 'rb') as f: 
                db_content = orjson.loads(f.read())
            
            try:
                coll = self.manager.get_collection(name=self.coll_names[media_type])
                res = coll.get(include=['metadatas'])
            except Exception as e:
                logger.error(f"Error getting collection {media_type} in load_catalog: {e}")
                res = {"metadatas": []}

            catalog = {
                "lookup": res['metadatas'],
                "db": db_content,
                "id_to_full_data": {str(item['id']): item for item in db_content}
            }
            self._catalog_cache[media_type] = catalog
            return catalog
        except Exception as e:
            logger.error(f"Catalog Load Error for {media_type}: {e}")
            return None

    def upsert_items(self, collection_name: str, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict]):
        try:
            coll = self.manager.get_collection(name=collection_name)
            coll.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas)
        except Exception as e:
            logger.error(f"PGVector Upsert Error in {collection_name}: {e}")

    def delete_collection(self, collection_name: str):
        try:
            self.manager.delete_collection(collection_name)
        except Exception as e:
            logger.error(f"PGVector Delete Error for {collection_name}: {e}")

    def get_collection_count(self, collection_name: str) -> int:
        try:
            coll = self.manager.get_collection(collection_name)
            return coll.count()
        except Exception as e:
            logger.exception(f"Error getting collection count for {collection_name}: {e}")
            return 0

    def get_all_ids(self, collection_name: str) -> List[str]:
        try:
            return list(self.manager.get_all_ids(collection_name))
        except Exception as e:
            logger.exception(f"Error getting all IDs for {collection_name}: {e}")
            return []

    def get_media_item(self, media_type: str, external_id: str) -> Optional[Dict]:
        catalog = self.load_catalog(media_type)
        if catalog:
            return catalog['id_to_full_data'].get(str(external_id))
        return None

    def get_catalog_by_type(self, media_type: str, limit: int = 1000) -> List[Dict]:
        catalog = self.load_catalog(media_type)
        if catalog:
            return list(catalog['id_to_full_data'].values())[:limit]
        return []

    def load_themes(self) -> Dict:
        path = os.path.join(self.project_root, "data", "processed", "anime_themes.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return orjson.loads(f.read())
        return {}

    def load_covers(self) -> Dict:
        path = os.path.join(self.project_root, "data", "processed", "manga_covers.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return orjson.loads(f.read())
        return {}

    def search_media_items(self, query: str, media_type: Optional[str] = None, limit: int = 10, offset: int = 0) -> List[Dict]:
        if not media_type:
            media_type = 'Anime'
            
        coll_name = self.coll_names.get(media_type)
        if not coll_name:
            return []
            
        try:
            coll = self.manager.get_collection(name=coll_name)
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

    def load_latent_space(self, media_type: str, vibe_type: str) -> Optional[Dict]:
        media = media_type.lower()
        vibe = vibe_type.lower()
        file_map = {
            'anime': {'thematic': 'latent_space_anime_thematic.json', 'visual': 'latent_space_anime_visual_vibe.json', 'scenario': 'latent_space_anime_plot.json'}, 
            'manga': {'thematic': 'latent_space_manga_thematic.json', 'visual': 'latent_space_manga_visual_vibe.json', 'scenario': 'latent_space_manga_plot.json'}, 
            'character': {'thematic': 'latent_space_character_vibe.json', 'visual': 'latent_space_character_visual_vibe.json'}
        }
        filename = file_map.get(media, file_map['anime']).get(vibe, 'latent_space_anime_thematic.json')
        data_path = os.path.join(self.project_root, 'data', 'artifacts', filename)
        if not os.path.exists(data_path):
            data_path = os.path.join(self.project_root, 'data', 'artifacts', 'latent_space_3d.json')
        if os.path.exists(data_path):
            with open(data_path, 'r', encoding='utf-8') as f:
                import json
                return json.load(f)
        return None

    def sync_latent_space(self, media_type: str, vibe_type: str, data: List[Dict]) -> int:
        logger.info(f"PGVector sync_latent_space: Stored {len(data)} items for {media_type}:{vibe_type}.")
        return len(data)

    def get_creative_fusion(self, fusion_id: int) -> Optional[Dict]:
        return None

    def get_user_gameplay_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        return []

    def get_user_creative_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        return []
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\pytest tests/core/test_pgvector_adapter.py -v`
Expected: PASS

- [ ] **Step 5: Clean up old files and commit**

Run git deletion for chroma-related adapter and tests:
```bash
git rm backend/adapters/persistence/chroma_repository_adapter.py
git rm tests/core/test_chroma_adapter.py
git add backend/adapters/persistence/pgvector_repository_adapter.py tests/core/test_pgvector_adapter.py
git commit -m "feat: implement pgvector repository adapter and delete old chroma files"
```

---

### Task 5: Unified Repository Integration

**Files:**
- Modify: [unified_repository_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/persistence/unified_repository_adapter.py)
- Modify: [persistence.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix/containers/persistence.py)
- Modify: [test_next_gen.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/tests/pipeline/test_next_gen.py)

- [ ] **Step 1: Write test for wiring**

Modify `tests/pipeline/test_next_gen.py` to patch `PGVectorRepositoryAdapter` instead of `ChromaRepositoryAdapter`. Replace `mock_chroma` patch lines (44-70) with PGVector mocks.

- [ ] **Step 2: Modify `unified_repository_adapter.py`**

Modify `backend/adapters/persistence/unified_repository_adapter.py` to replace `ChromaRepositoryAdapter` with `PGVectorRepositoryAdapter`:

```python
import logging
from typing import List, Dict, Optional
from core.ports.repository_port import RepositoryPort
from .pgvector_repository_adapter import PGVectorRepositoryAdapter
from .django_repository_adapter import DjangoRepositoryAdapter

logger = logging.getLogger('animetix')

class UnifiedRepositoryAdapter(RepositoryPort):
    def __init__(self, chroma_db_path: str, project_root: str):
        self.project_root = project_root
        self.chroma = PGVectorRepositoryAdapter(project_root=project_root)
        self.django = DjangoRepositoryAdapter()
        logger.info("Using PGVector as primary vector repository adapter.")

    def _get_primary(self) -> RepositoryPort:
        return self.chroma

    def get_nearest_neighbors(self, collection_name: str, item_id: str, n_results: int = 5) -> Optional[Dict]:
        return self.chroma.get_nearest_neighbors(collection_name, item_id, n_results)

    def calculate_similarity(self, collection_name: str, item_a_id: str, item_b_id: str) -> float:
        return self.chroma.calculate_similarity(collection_name, item_a_id, item_b_id)

    def load_catalog(self, media_type: str) -> Optional[Dict]:
        return self.chroma.load_catalog(media_type)

    def load_themes(self) -> Dict:
        return self.django.load_themes()

    def load_covers(self) -> Dict:
        return self.django.load_covers()

    def get_media_item(self, media_type: str, external_id: str) -> Optional[Dict]:
        return self.django.get_media_item(media_type, external_id)

    def search_media_items(self, query: str, media_type: Optional[str] = None, limit: int = 10, offset: int = 0) -> List[Dict]:
        results = self.chroma.search_media_items(query, media_type, limit, offset)
        if results:
            return results
        return self.django.search_media_items(query, media_type, limit, offset)

    def upsert_items(self, collection_name: str, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict]):
        self.chroma.upsert_items(collection_name, ids, embeddings, metadatas)

    def delete_collection(self, collection_name: str):
        self.chroma.delete_collection(collection_name)

    def get_collection_count(self, collection_name: str) -> int:
        return self.chroma.get_collection_count(collection_name)

    def get_all_ids(self, collection_name: str) -> List[str]:
        return self.chroma.get_all_ids(collection_name)

    def get_catalog_by_type(self, media_type: str, limit: int = 1000, offset: int = 0) -> List[Dict]:
        return self.django.get_catalog_by_type(media_type, limit, offset)

    def load_latent_space(self, media_type: str, vibe_type: str) -> Optional[Dict]:
        db_res = self.django.load_latent_space(media_type, vibe_type)
        if db_res:
            return db_res
        return self.chroma.load_latent_space(media_type, vibe_type)

    def sync_latent_space(self, media_type: str, vibe_type: str, data: List[Dict]) -> int:
        return self.django.sync_latent_space(media_type, vibe_type, data)

    def get_creative_fusion(self, fusion_id: int) -> Optional[Dict]:
        return self.django.get_creative_fusion(fusion_id)

    def get_user_gameplay_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        return self.django.get_user_gameplay_history(user_id, limit)

    def get_user_creative_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        return self.django.get_user_creative_history(user_id, limit)
```

- [ ] **Step 3: Modify `persistence.py`**

In `backend/api/animetix/containers/persistence.py`, remove unnecessary references if any. The `UnifiedRepositoryAdapter` instantiation remains the same:
`chroma_db_path=settings.CHROMA_DB_PATH` is passed but will simply be unused by `PGVectorRepositoryAdapter`.

- [ ] **Step 4: Run tests to verify correctness**

Run: `.venv\Scripts\pytest tests/core/test_long_term_memory_service.py tests/pipeline/test_next_gen.py -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add backend/adapters/persistence/unified_repository_adapter.py tests/pipeline/test_next_gen.py
git commit -m "feat: integrate PGVectorRepositoryAdapter into unified adapter flow"
```

---

### Task 6: Dependency and Infrastructure Cleanup

**Files:**
- Modify: [requirements.txt](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/requirements.txt)
- Modify: [docker-compose.yml](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/deploy/docker-compose.yml)

- [ ] **Step 1: Modify `requirements.txt`**

Remove `chromadb==1.5.5` from `requirements.txt`.

- [ ] **Step 2: Modify `deploy/docker-compose.yml`**

Replace `image: postgres:16-alpine` with `image: pgvector/pgvector:pg16` for local dev.
Delete the `chromadb` service configuration block entirely.
Remove `chromadb` from the `depends_on` list in the `web` and `celery_worker` services.

- [ ] **Step 3: Run full tests to verify zero regressions**

Run: `.venv\Scripts\pytest tests/ -v`
Expected: All tests pass successfully.

- [ ] **Step 4: Commit changes**

```bash
git add requirements.txt deploy/docker-compose.yml
git commit -m "refactor: remove chromadb container and dependency, upgrade postgres image to pgvector"
```
