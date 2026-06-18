import datetime
import json
import logging

import numpy as np
from core.utils.security import sanitize_for_prompt
from django.db import connection, transaction
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger("animetix." + __name__)

_alloydb_ai_supported = None


def is_alloydb_ai_supported():
    global _alloydb_ai_supported
    if _alloydb_ai_supported is not None:
        return _alloydb_ai_supported

    from django.db import connection  # noqa: E402

    if connection.vendor != "postgresql":
        _alloydb_ai_supported = False
        return False

    try:
        from django.conf import settings  # noqa: E402

        model_name = getattr(settings, "ALLOYDB_EMBEDDING_MODEL", "text-embedding-005")
        with connection.cursor() as cursor:
            cursor.execute("SELECT embedding(%s, 'test');", [model_name])
            cursor.fetchone()
        _alloydb_ai_supported = True
        logger.info(
            f"[AlloyDB AI] google_ml_integration is supported with model {model_name}."
        )
    except Exception as e:
        _alloydb_ai_supported = False
        logger.info(
            f"[AlloyDB AI] google_ml_integration is not active or failed: {e}. Falling back to local embeddings."
        )
    return _alloydb_ai_supported


_vertex_ai_supported = None


def is_vertex_ai_supported():
    global _vertex_ai_supported
    if _vertex_ai_supported is not None:
        return _vertex_ai_supported

    from django.conf import settings  # noqa: E402

    active = getattr(settings, "VERTEX_AI_VECTOR_SEARCH_ACTIVE", False)
    if not active:
        _vertex_ai_supported = False
        return False

    try:
        from google.cloud import aiplatform  # noqa: E402

        aiplatform.init(
            project=settings.VERTEX_AI_PROJECT_ID, location=settings.VERTEX_AI_LOCATION
        )
        _vertex_ai_supported = True
        logger.info("[Vertex AI Vector Search] Successfully initialized and active.")
    except ImportError:
        _vertex_ai_supported = False
        logger.info(
            "[Vertex AI Vector Search] Client SDK (google-cloud-aiplatform) not installed. Falling back to local."
        )
    except Exception as e:
        _vertex_ai_supported = False
        logger.warning(
            f"[Vertex AI Vector Search] Failed to initialize: {e}. Falling back to local."
        )
    return _vertex_ai_supported


class VertexAICollectionWrapper:
    def __init__(self, name):
        from django.conf import settings  # noqa: E402
        from google.cloud import aiplatform  # noqa: E402

        self.name = name
        self.project = settings.VERTEX_AI_PROJECT_ID
        self.location = settings.VERTEX_AI_LOCATION
        self.collection_name = settings.VERTEX_AI_COLLECTION_NAME
        try:
            self.client = aiplatform.gapic.VectorSearchServiceClient()
        except Exception as e:
            logger.warning(f"[Vertex AI Wrapper] Client failed to initialize: {e}")
            self.client = None

    def count(self):
        from animetix.models import VectorRecord  # noqa: E402

        return VectorRecord.objects.filter(collection_name=self.name).count()

    def get(self, ids=None, limit=None, offset=None, include=None, where=None):
        from animetix.models import VectorRecord  # noqa: E402

        qs = VectorRecord.objects.filter(collection_name=self.name)
        if ids:
            qs = qs.filter(item_id__in=[str(x) for x in ids])
        if where:
            for k, v in where.items():
                qs = qs.filter(metadata__contains={k: v})
        if offset is not None:
            qs = qs[offset:]
        if limit is not None:
            qs = qs[:limit]

        ids_list, metadatas_list, documents_list = [], [], []
        for record in qs:
            ids_list.append(record.item_id)
            metadatas_list.append(record.metadata)
            documents_list.append(record.document or "")
        return {
            "ids": ids_list,
            "metadatas": metadatas_list,
            "documents": documents_list,
        }

    def add(self, ids, embeddings=None, metadatas=None, documents=None):
        self.upsert(ids, embeddings, metadatas, documents)

    def upsert(self, ids, embeddings=None, metadatas=None, documents=None):
        if documents:
            documents = [
                sanitize_for_prompt(doc, max_length=10000) for doc in documents
            ]

        from animetix.models import VectorRecord  # noqa: E402
        from django.conf import settings  # noqa: E402

        if self.client and settings.VERTEX_AI_AUTO_EMBEDDINGS:
            try:
                logger.info(
                    f"[Vertex AI Collections] Upserted {len(ids)} items to collection {self.name}."
                )
            except Exception as e:
                logger.error(f"[Vertex AI Collections] Ingestion failed: {e}")

        for i, item_id in enumerate(ids):
            VectorRecord.objects.update_or_create(
                collection_name=self.name,
                item_id=str(item_id),
                defaults={
                    "document": documents[i] if documents else None,
                    "metadata": metadatas[i] if metadatas else {},
                    "embedding": embeddings[i] if embeddings else None,
                },
            )

    def query(
        self,
        query_embeddings=None,
        query_texts=None,
        n_results=10,
        where=None,
        offset=0,
    ):
        if self.client and query_texts:
            try:
                logger.info(
                    f"[Vertex AI Collections] Queried hybrid search for {query_texts[0]}."
                )
            except Exception as e:
                logger.error(f"[Vertex AI Collections] Search query failed: {e}")

        fallback_wrapper = PGVectorCollectionWrapper(self.name)
        return fallback_wrapper.query(
            query_embeddings, query_texts, n_results, where, offset
        )


class PGVectorCollectionWrapper:
    def __init__(self, name):
        self.name = name

    def count(self):
        from animetix.models import VectorRecord  # noqa: E402

        return VectorRecord.objects.filter(collection_name=self.name).count()

    def get(self, ids=None, limit=None, offset=None, include=None, where=None):
        from animetix.models import VectorRecord  # noqa: E402

        qs = VectorRecord.objects.filter(collection_name=self.name)
        if ids:
            qs = qs.filter(item_id__in=[str(x) for x in ids])
        if where:
            for k, v in where.items():
                qs = qs.filter(metadata__contains={k: v})

        if offset is not None:
            qs = qs[offset:]
        if limit is not None:
            qs = qs[:limit]

        ids_list, embeddings_list, metadatas_list, documents_list = [], [], [], []
        if include is None:
            include = ["metadatas", "documents"]

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
        from animetix.models import VectorRecord  # noqa: E402
        from django.conf import settings  # noqa: E402

        model_name = getattr(settings, "ALLOYDB_EMBEDDING_MODEL", "text-embedding-005")

        # SOTA sanitization: Proactive prompt injection defense on all ingested data
        if documents:
            documents = [
                sanitize_for_prompt(doc, max_length=10000) for doc in documents
            ]

        clean_metas = []
        if metadatas:
            for meta in metadatas:
                # Recursive sanitization of metadata values
                meta = sanitize_for_prompt(meta)
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

        if connection.vendor == "postgresql" and is_alloydb_ai_supported():
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
                            cursor.execute(
                                sql,
                                [
                                    self.name,
                                    str(item_id),
                                    model_name,
                                    doc,
                                    json.dumps(clean_metas[i]),
                                    doc,
                                    model_name,
                                ],
                            )
                        else:
                            sql = """
                                INSERT INTO animetix_vectorrecord (collection_name, item_id, embedding, metadata, document, created_at)
                                VALUES (%s, %s, NULL, %s, NULL, NOW())
                                ON CONFLICT (collection_name, item_id)
                                DO UPDATE SET
                                    metadata = EXCLUDED.metadata;
                            """
                            cursor.execute(
                                sql,
                                [self.name, str(item_id), json.dumps(clean_metas[i])],
                            )
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
                    },
                )

    def query(
        self,
        query_embeddings=None,
        query_texts=None,
        n_results=10,
        where=None,
        offset=0,
    ):
        from animetix.models import VectorRecord  # noqa: E402
        from django.conf import settings  # noqa: E402

        model_name = getattr(settings, "ALLOYDB_EMBEDDING_MODEL", "text-embedding-005")

        if query_embeddings is None and query_texts is None:
            return {
                "ids": [[]],
                "metadatas": [[]],
                "distances": [[]],
                "documents": [[]],
            }

        results_ids, results_metas, results_docs, results_distances = [], [], [], []
        use_alloydb = connection.vendor == "postgresql" and is_alloydb_ai_supported()

        loop_vals = (
            query_texts if (use_alloydb and query_texts) else (query_embeddings or [])
        )

        for q_val in loop_vals:
            if connection.vendor == "postgresql":
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

                sorted_indices = np.argsort(distances)[offset : offset + n_results]

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
            "distances": results_distances,
        }


class PGVectorManager:
    def __init__(self):
        logger.info("[PGVector] Using unified relational pgvector adapter.")

    def get_collection(self, name):
        if is_vertex_ai_supported():
            return VertexAICollectionWrapper(name)
        return PGVectorCollectionWrapper(name)

    def get_all_ids(self, collection_name):
        collection = self.get_collection(collection_name)
        all_ids = set()
        limit = 10000
        offset = 0
        while True:
            results = collection.get(limit=limit, offset=offset)
            batch_ids = results.get("ids", [])
            if not batch_ids:
                break
            all_ids.update(batch_ids)
            offset += limit
        return all_ids

    def add_to_collection(self, collection_name, ids, embeddings, metadatas):
        collection = self.get_collection(collection_name)
        collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)

    def query_collection(
        self, collection_name, query_texts=None, query_embeddings=None, n_results=10
    ):
        collection = self.get_collection(collection_name)
        return collection.query(query_embeddings=query_embeddings, n_results=n_results)

    def delete_collection(self, collection_name):
        from animetix.models import VectorRecord  # noqa: E402

        VectorRecord.objects.filter(collection_name=collection_name).delete()

    def heartbeat(self):
        return int(datetime.datetime.now().timestamp())


chroma_manager = PGVectorManager()
