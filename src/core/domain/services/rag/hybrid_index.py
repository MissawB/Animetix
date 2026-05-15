import numpy as np
from typing import List, Dict, Optional
from sklearn.feature_extraction.text import TfidfVectorizer

class HybridSearchIndex:
    """
    Gère l'indexation lexicale (BM25/TF-IDF) avec support du RAG Hiérarchique 
    et du Contextual Retrieval.
    """
    def __init__(self):
        self.vectorizer = TfidfVectorizer(use_idf=True, smooth_idf=True)
        self.matrix = None
        self.chunks = []
        self.parent_child_map = {}
        self._context_headers = {}

    def is_initialized(self) -> bool:
        return self.matrix is not None

    def initialize(self, items: List[Dict], media_type: str):
        """Construit l'index à partir d'une liste de médias."""
        documents = []
        for item in items:
            context_header = self._generate_context_header(item, media_type)
            
            full_text = f"{item.get('title', '')} {item.get('description', '')}"
            item_chunks = self._chunk_text(full_text, size=300)
            
            for chunk in item_chunks:
                contextual_chunk = (context_header + chunk).lower()
                self.parent_child_map[contextual_chunk] = item
                documents.append(contextual_chunk)
        
        if documents:
            self.matrix = self.vectorizer.fit_transform(documents)
            self.chunks = documents

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Exécute une recherche lexicale et retourne les parents uniques."""
        if not self.is_initialized():
            return []
            
        query_vec = self.vectorizer.transform([query.lower()])
        scores = (self.matrix * query_vec.T).toarray().flatten()
        
        top_indices = np.argsort(scores)[::-1][:limit*2]
        
        seen_parents = set()
        results = []
        for i in top_indices:
            if scores[i] <= 0: continue
            chunk = self.chunks[i]
            parent = self.parent_child_map.get(chunk)
            if parent and parent['id'] not in seen_parents:
                results.append(parent)
                seen_parents.add(parent['id'])
                if len(results) >= limit: break
                
        return results

    def _generate_context_header(self, item: Dict, media_type: str) -> str:
        title = item.get('title') or item.get('name', 'Inconnu')
        key = f"{media_type}:{title}"
        
        if key in self._context_headers:
            return self._context_headers[key]
            
        context = f"[Document: {title} | Type: {media_type}] "
        genres = item.get('genres', [])[:2]
        if genres:
            context += f"Genre: {', '.join(genres)}. "
            
        self._context_headers[key] = context
        return context

    def _chunk_text(self, text: str, size: int) -> List[str]:
        return [text[i:i+size] for i in range(0, len(text), size)]
