import logging
from typing import Optional, List
from core.ports.inference_port import InferencePort
from core.ports.cache_port import SemanticCachePort

logger = logging.getLogger('animetix.cache')

class SemanticCacheService:
    """
    Service de mise en cache sémantique pour réduire les coûts et la latence des appels LLM.
    Utilise un port de persistance (SemanticCachePort) pour isoler le domaine de l'infrastructure Django.
    """
    def __init__(self, inference_engine: Optional[InferencePort] = None, cache_port: Optional[SemanticCachePort] = None):
        self.inference_engine = inference_engine
        self.cache_port = cache_port
        self.similarity_threshold = 0.92

    def get_cached_response(self, query: str) -> Optional[str]:
        """Cherche une réponse en cache via correspondance exacte ou similarité sémantique."""
        if not self.cache_port:
            return None
            
        try:
            # 1. Tentative de correspondance exacte (très rapide)
            exact = self.cache_port.get(query)
            if exact:
                logger.info(f"⚡ [Cache] Exact hit for: {query[:50]}...")
                return exact

            # 2. Si on a un moteur d'inférence pour les embeddings, on tente le vectoriel
            if self.inference_engine and hasattr(self.inference_engine, 'get_text_embedding'):
                emb = self.inference_engine.get_text_embedding(query)
                res = self.cache_port.get_semantic(emb, self.similarity_threshold)
                if res:
                    logger.info("🧠 [Cache] Semantic hit")
                    return res
                        
            return None
        except Exception as e:
            logger.error(f"Cache Retrieval Error: {e}")
            return None

    def set_cached_response(self, query: str, response: str):
        """Stocke une réponse dans le cache avec son embedding."""
        if not self.cache_port:
            return

        try:
            emb = []
            if self.inference_engine and hasattr(self.inference_engine, 'get_text_embedding'):
                emb = self.inference_engine.get_text_embedding(query)
            
            self.cache_port.set(query, emb, response)
            logger.info(f"💾 [Cache] Stored response for: {query[:50]}...")
        except Exception as e:
            logger.error(f"Cache Storage Error: {e}")
