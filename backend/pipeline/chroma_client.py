import logging
import datetime
import json
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
