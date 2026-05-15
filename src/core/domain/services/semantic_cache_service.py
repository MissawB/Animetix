import logging
import hashlib
from typing import Optional, Dict

logger = logging.getLogger('animetix.cache')

class SemanticCacheService:
    """
    Implémentation d'un Cache Sémantique via ChromaDB (concept type GPTCache).
    Évite de régénérer via le LLM des requêtes sémantiquement identiques.
    """
    def __init__(self, chroma_resource):
        self.chroma = chroma_resource
        self.collection_name = "semantic_cache"
        self.similarity_threshold = 0.92 # Seuil de pertinence élevé pour le cache (Cosine distance faible)

    def _get_collection(self):
        return self.chroma.get_collection(self.collection_name)

    def get_cached_response(self, query: str) -> Optional[str]:
        """Cherche une réponse en cache avec une similarité > 92%."""
        try:
            coll = self._get_collection()
            results = coll.query(
                query_texts=[query],
                n_results=1
            )
            
            if not results['documents'] or not results['documents'][0]:
                return None
                
            distance = results['distances'][0][0]
            # ChromaDB utilise souvent la distance L2 ou Cosine. 
            # Plus c'est bas, plus c'est similaire.
            # Convertissons la distance cosinus en similarité (approx: 1 - distance)
            similarity = 1.0 - distance
            
            if similarity >= self.similarity_threshold:
                logger.info(f"⚡ [Semantic Cache Hit] Similarity: {similarity:.2f}")
                return results['documents'][0][0]
                
            return None
        except Exception as e:
            logger.error(f"Semantic Cache Retrieval Error: {e}")
            return None

    def set_cached_response(self, query: str, response: str):
        """Stocke une réponse fraîchement générée dans le cache vectoriel."""
        try:
            coll = self._get_collection()
            # On crée un ID déterministe pour éviter les doublons exacts
            query_id = hashlib.md5(query.encode('utf-8')).hexdigest()
            
            coll.add(
                ids=[query_id],
                documents=[response],
                metadatas=[{"query": query}]
            )
        except Exception as e:
            logger.error(f"Semantic Cache Storage Error: {e}")
