import logging
from typing import Dict, List

from adapters.persistence.cache_constants import COLLECTION_COUNT_CACHE_TTL_SECONDS
from core.domain.exceptions import InfrastructureError
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
        """Cherche les plus proches voisins. LÈVE si la requête échoue.

        Cette méthode avalait toute exception et rendait `[]`. Or l'appelant
        (la recherche visuelle) facture AVANT de chercher : une panne pgvector
        devenait un 200 avec zéro résultat, impossible à distinguer d'un
        « aucune correspondance ». L'utilisateur payait, lisait « rien trouvé »,
        et la panne ne laissait aucune trace côté réponse.

        Une liste vide veut dire « la requête a tourné et n'a rien trouvé », et
        uniquement ça. Tout le reste lève — l'appelant (la vue) transforme déjà
        une exception en 500.
        """
        try:
            collection = vector_manager.get_collection(collection_name)
            res = collection.query(query_embeddings=[query_vector], n_results=limit)
        except Exception as e:
            logger.exception(
                f"Vector search failed for collection '{collection_name}': {e}"
            )
            raise InfrastructureError(
                f"La recherche vectorielle dans « {collection_name} » a échoué : "
                f"{e}. Refus de rendre une liste vide — elle passerait pour "
                "« aucun résultat » alors que la requête n'a jamais abouti."
            ) from e

        results: List[Dict] = []
        if res and res.get("metadatas") and res["metadatas"][0]:
            for meta, doc_id in zip(res["metadatas"][0], res["ids"][0]):
                doc = dict(meta)
                doc["id"] = doc_id
                results.append(doc)
        return results

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
