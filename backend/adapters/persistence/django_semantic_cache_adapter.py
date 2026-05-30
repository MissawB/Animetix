from typing import Optional, List
import logging
from core.ports.cache_port import SemanticCachePort

logger = logging.getLogger('animetix.adapters')

class DjangoSemanticCacheAdapter(SemanticCachePort):
    def get(self, query: str) -> Optional[str]:
        from animetix.models import SemanticCache
        exact = SemanticCache.objects.filter(query_text=query).first()
        return exact.response_text if exact else None

    def get_semantic(self, query_embedding: List[float], threshold: float) -> Optional[str]:
        """
        Désactivé dans l'adaptateur relationnel.
        ChromaDB devrait être utilisé pour le cache sémantique si nécessaire.
        """
        return None

    def set(self, query: str, query_embedding: List[float], response: str) -> None:
        from animetix.models import SemanticCache
        SemanticCache.objects.update_or_create(
            query_text=query,
            defaults={
                'response_text': response
            }
        )
