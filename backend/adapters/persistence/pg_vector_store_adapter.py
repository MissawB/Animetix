from typing import List

from core.ports.vector_store_port import VectorStorePort
from pipeline.vector_client import vector_manager


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
