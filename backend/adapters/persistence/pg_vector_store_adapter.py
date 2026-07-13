import logging
from typing import Dict, List

from adapters.persistence.cache_constants import COLLECTION_COUNT_CACHE_TTL_SECONDS
from core.ports.vector_store_port import VectorStorePort
from django.core.cache import cache
from pipeline.vector_client import vector_manager

logger = logging.getLogger("animetix.vector_store")


class PgVectorStoreAdapter(VectorStorePort):
    """Adapter pgvector vers `VectorStorePort`.

    Unique point où `pipeline.vector_client` est référencé : le `core` ne dépend
    que du port abstrait.
    """

    def get_embeddings(self, collection_name: str, limit: int) -> List[List[float]]:
        collection = vector_manager.get_collection(collection_name)
        data = collection.get(include=["embeddings"], limit=limit)
        if not data or not data.get("embeddings"):
            return []
        return data["embeddings"]

    def search_by_vector(
        self, collection_name: str, query_vector: List[float], limit: int = 10
    ) -> List[Dict]:
        try:
            collection = vector_manager.get_collection(collection_name)
            res = collection.query(query_embeddings=[query_vector], n_results=limit)
            results: List[Dict] = []
            if res and res.get("metadatas") and res["metadatas"][0]:
                for meta, doc_id in zip(res["metadatas"][0], res["ids"][0]):
                    doc = dict(meta)
                    doc["id"] = doc_id
                    results.append(doc)
            return results
        except Exception as e:
            logger.error(
                f"Vector search failed for collection '{collection_name}': {e}"
            )
            return []

    def get_collection_count(self, collection_name: str) -> int:
        cache_key = f"vsp_collection_count_{collection_name}"

        try:
            cached = cache.get(cache_key)
        except Exception as e:
            # The cache is an optimisation, not a dependency: a Redis blip
            # must degrade to a live COUNT, not to a 500 for callers that
            # don't otherwise need Redis.
            logger.warning(f"Cache read failed for '{cache_key}': {e}")
            cached = None
        if cached is not None:
            return int(cached)

        try:
            collection = vector_manager.get_collection(collection_name)
            count = collection.count()
        except Exception as e:
            # A failure to ask the database is NOT the same fact as "I asked,
            # and it is empty" -- caching a 0 here would memoise a transient
            # outage as "the index doesn't exist" for the full TTL. Fail
            # closed for *this* request only, without remembering it.
            logger.error(f"Failed to count collection '{collection_name}': {e}")
            return 0

        try:
            cache.set(cache_key, count, timeout=COLLECTION_COUNT_CACHE_TTL_SECONDS)
        except Exception as e:
            logger.warning(f"Cache write failed for '{cache_key}': {e}")

        return count
