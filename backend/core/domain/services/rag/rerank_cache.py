import hashlib
import logging
from typing import Dict, List, Optional

from core.ports.generic_cache_port import CachePort, InMemoryCache

logger = logging.getLogger("animetix.rerank.cache")


class RerankingCache:
    """
    Cache pour les scores de reranking (Cross-Encoder).
    Réduit la latence en évitant de ré-évaluer les mêmes paires (Requête, Document).
    """

    def __init__(
        self,
        ttl: int = 60 * 60 * 24,  # 24 heures par défaut
        cache_port: Optional[CachePort] = None,
    ):
        self.ttl = ttl
        self.cache = cache_port or InMemoryCache()

    def get_scores(self, query: str, doc_ids: List[str]) -> Dict[str, float]:
        """Récupère les scores cachés pour une requête et une liste d'IDs."""
        results = {}
        query_hash = self._hash(query)

        # On tente de récupérer chaque score individuellement
        # Clé: rr:{query_hash}:{doc_id}
        keys = [f"rr:{query_hash}:{did}" for did in doc_ids]
        cached_values = self.cache.get_many(keys)

        for did in doc_ids:
            key = f"rr:{query_hash}:{did}"
            if key in cached_values:
                results[did] = cached_values[key]

        if results:
            logger.debug(
                f"🎯 Rerank Cache: {len(results)}/{len(doc_ids)} hits for query hash {query_hash}"
            )

        return results

    def set_scores(self, query: str, scores_map: Dict[str, float]):
        """Stocke les scores calculés dans le cache."""
        query_hash = self._hash(query)
        data_to_cache = {
            f"rr:{query_hash}:{did}": score for did, score in scores_map.items()
        }
        self.cache.set_many(data_to_cache, timeout=self.ttl)

    def _hash(self, text: str) -> str:
        return hashlib.md5(
            text.lower().strip().encode(), usedforsecurity=False
        ).hexdigest()
