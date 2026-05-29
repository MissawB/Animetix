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
        from animetix.models import SemanticCache
        from django.db.models import F
        match = SemanticCache.objects.annotate(
            sim=1 - F('query_embedding').cosine_distance(query_embedding)
        ).filter(sim__gte=threshold).order_by('-sim').first()
        
        return match.response_text if match else None

    def set(self, query: str, query_embedding: List[float], response: str) -> None:
        from animetix.models import SemanticCache
        SemanticCache.objects.update_or_create(
            query_text=query,
            defaults={
                'query_embedding': query_embedding,
                'response_text': response
            }
        )
