import logging
from typing import Dict, List

from core.ports.vector_store_port import VectorStorePort
from django.core.cache import cache
from pipeline.vector_client import vector_manager

logger = logging.getLogger("animetix.vector_store")

# TTL du cache "la collection a-t-elle des vecteurs ?". Cette question est
# posée avant chaque recherche payante (garde-fou anti-facturation d'un index
# vide) -- sans cache, ce serait une requête COUNT(*) de plus par recherche.
# 60s suffit : il ne s'agit que de détecter si l'index a été construit, pas de
# suivre un compteur exact en temps réel (un backfill met alors jusqu'à 60s à
# "débloquer" la recherche -- c'est le compromis accepté).
_COLLECTION_COUNT_CACHE_TTL = 60


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
        cached = cache.get(cache_key)
        if cached is not None:
            return int(cached)

        try:
            collection = vector_manager.get_collection(collection_name)
            count = collection.count()
        except Exception as e:
            logger.error(f"Failed to count collection '{collection_name}': {e}")
            count = 0

        cache.set(cache_key, count, timeout=_COLLECTION_COUNT_CACHE_TTL)
        return count
