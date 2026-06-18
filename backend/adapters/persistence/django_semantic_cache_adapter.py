import hashlib
import logging
from typing import List, Optional

from core.ports.cache_port import SemanticCachePort

logger = logging.getLogger("animetix.adapters")


class DjangoSemanticCacheAdapter(SemanticCachePort):
    def __init__(self, collection_name: str = "semantic_cache"):
        self.collection_name = collection_name

    def get(self, query: str) -> Optional[str]:
        from animetix.models import SemanticCache  # noqa: E402

        exact = SemanticCache.objects.filter(query_text=query).first()
        return exact.response_text if exact else None

    def get_semantic(
        self, query_embedding: List[float], threshold: float
    ) -> Optional[str]:
        """
        Récupère la réponse la plus proche sémantiquement en utilisant le Vector Store unifié.
        """
        if not query_embedding:
            return None

        from pipeline.chroma_client import chroma_manager  # noqa: E402

        try:
            results = chroma_manager.query_collection(
                collection_name=self.collection_name,
                query_embeddings=[query_embedding],
                n_results=1,
            )

            distances = results.get("distances", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]

            if distances and metadatas and len(distances) > 0:
                distance = distances[0]
                # Le Vector Store retourne généralement une distance cosinus (0 = identique)
                # Similarité = 1 - distance
                similarity = 1.0 - float(distance)

                if similarity >= threshold:
                    meta = metadatas[0]
                    # Gérer le cas où les métadonnées sont retournées comme une chaîne JSON (selon le backend)
                    if isinstance(meta, str):
                        import json  # noqa: E402

                        try:
                            meta = json.loads(meta)
                        except json.JSONDecodeError:
                            return None

                    if isinstance(meta, dict) and "response" in meta:
                        return meta["response"]
        except Exception as e:
            logger.error(f"❌ Semantic cache vector retrieval failed: {e}")

        return None

    def set(self, query: str, query_embedding: List[float], response: str) -> None:
        from animetix.models import SemanticCache  # noqa: E402
        from pipeline.chroma_client import chroma_manager  # noqa: E402

        # 1. Sauvegarde relationnelle (pour correspondance exacte)
        SemanticCache.objects.update_or_create(
            query_text=query, defaults={"response_text": response}
        )

        # 2. Sauvegarde vectorielle (pour similarité sémantique)
        if query_embedding:
            query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
            try:
                chroma_manager.add_to_collection(
                    collection_name=self.collection_name,
                    ids=[query_hash],
                    embeddings=[query_embedding],
                    metadatas=[{"response": response, "query": query}],
                )
            except Exception as e:
                logger.error(f"❌ Failed to set semantic cache in vector store: {e}")
