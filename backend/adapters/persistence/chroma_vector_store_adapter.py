from typing import List

from core.ports.vector_store_port import VectorStorePort
from pipeline.chroma_client import chroma_manager


class ChromaVectorStoreAdapter(VectorStorePort):
    """Adapter ChromaDB vers `VectorStorePort`.

    Unique point où `pipeline.chroma_client` est référencé : le `core` ne dépend
    que du port abstrait.
    """

    def get_embeddings(self, collection_name: str, limit: int) -> List[List[float]]:
        collection = chroma_manager.get_collection(collection_name)
        data = collection.get(include=["embeddings"], limit=limit)
        if not data or not data.get("embeddings"):
            return []
        return data["embeddings"]
