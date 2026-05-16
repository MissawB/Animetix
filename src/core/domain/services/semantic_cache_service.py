import logging
import hashlib
from typing import Optional
from django.conf import settings
from animetix.models import SemanticCache
import numpy as np

logger = logging.getLogger('animetix.cache')

class SemanticCacheService:
    """
    Cache sémantique utilisant le modèle Django SemanticCache.
    Si pgvector est disponible, utilise la recherche vectorielle, sinon fallback texte.
    """
    def __init__(self, inference_engine=None):
        self.inference_engine = inference_engine
        self.similarity_threshold = 0.92

    def get_cached_response(self, query: str) -> Optional[str]:
        """Cherche une réponse en cache via similarité sémantique."""
        try:
            # 1. Tentative de correspondance exacte (très rapide)
            exact = SemanticCache.objects.filter(query_text=query).first()
            if exact:
                logger.info(f"⚡ [Cache] Exact hit for: {query[:50]}...")
                return exact.response_text

            # 2. Si on a un moteur d'inférence pour les embeddings, on tente le vectoriel
            if self.inference_engine:
                # Note: On assume que l'inference_engine peut générer des embeddings 
                # (via une méthode non définie explicitement ici mais présente dans les adapters)
                if hasattr(self.inference_engine, 'get_text_embedding'):
                    emb = self.inference_engine.get_text_embedding(query)
                    
                    # Recherche via pgvector si possible
                    from django.db.models import F
                    # On cherche l'entrée la plus proche
                    # similarity = 1 - cosine_distance
                    match = SemanticCache.objects.annotate(
                        sim=1 - F('query_embedding').cosine_distance(emb)
                    ).filter(sim__gte=self.similarity_threshold).order_by('-sim').first()
                    
                    if match:
                        logger.info(f"🧠 [Cache] Semantic hit (sim: {match.sim:.2f})")
                        return match.response_text
                        
            return None
        except Exception as e:
            logger.error(f"Cache Retrieval Error: {e}")
            return None

    def set_cached_response(self, query: str, response: str):
        """Stocke une réponse dans le cache."""
        try:
            cache_entry, created = SemanticCache.objects.get_or_create(
                query_text=query,
                defaults={'response_text': response}
            )
            
            # Mise à jour de l'embedding si nécessaire
            if created and self.inference_engine and hasattr(self.inference_engine, 'get_text_embedding'):
                emb = self.inference_engine.get_text_embedding(query)
                cache_entry.query_embedding = emb
                cache_entry.save()
        except Exception as e:
            logger.error(f"Cache Storage Error: {e}")
