from typing import Dict, List

import numpy as np
from core.utils.lazy_import import lazy_import

# Lazy import for sklearn's TfidfVectorizer
sklearn_text = lazy_import("sklearn.feature_extraction.text")
TfidfVectorizer = sklearn_text.TfidfVectorizer


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

            title = item.get("title") or item.get("name") or ""
            desc = item.get("description") or item.get("clean_description") or ""
            full_text = f"{title} {desc}"
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

        top_indices = np.argsort(scores)[::-1][: limit * 2]

        seen_parents = set()
        results = []
        for i in top_indices:
            if scores[i] <= 0:
                continue
            chunk = self.chunks[i]
            parent = self.parent_child_map.get(chunk)
            if parent and parent["id"] not in seen_parents:
                results.append(parent)
                seen_parents.add(parent["id"])
                if len(results) >= limit:
                    break

        return results

    def search_with_scores(self, query: str, limit: int = 20) -> List[tuple]:
        """Exécute une recherche lexicale et retourne les parents avec leurs scores bruts."""
        if not self.is_initialized():
            return []

        query_vec = self.vectorizer.transform([query.lower()])
        scores = (self.matrix * query_vec.T).toarray().flatten()

        top_indices = np.argsort(scores)[::-1][: limit * 2]

        seen_parents = set()
        results = []
        for i in top_indices:
            if scores[i] <= 0:
                continue
            chunk = self.chunks[i]
            parent = self.parent_child_map.get(chunk)
            if parent and parent["id"] not in seen_parents:
                results.append((parent, float(scores[i])))
                seen_parents.add(parent["id"])
                if len(results) >= limit:
                    break

        return results

    @staticmethod
    def reciprocal_rank_fusion(
        lexical_list: List[Dict], semantic_list: List[Dict], k: int = 60
    ) -> List[Dict]:
        """Fusionne deux listes de résultats en utilisant le Reciprocal Rank Fusion (RRF)."""
        rrf_scores: Dict[str, float] = {}
        doc_map: Dict[str, Dict] = {}

        def get_doc_id(doc):
            return str(doc.get("id") or doc.get("external_id") or "")

        for rank, doc in enumerate(lexical_list):
            doc_id = get_doc_id(doc)
            if not doc_id:
                continue
            doc_map[doc_id] = doc
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)

        for rank, doc in enumerate(semantic_list):
            doc_id = get_doc_id(doc)
            if not doc_id:
                continue
            doc_map[doc_id] = doc
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)

        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return [doc_map[doc_id] for doc_id, score in sorted_docs]

    def _generate_context_header(self, item: Dict, media_type: str) -> str:
        title = item.get("title") or item.get("name", "Inconnu")
        key = f"{media_type}:{title}"

        if key in self._context_headers:
            return self._context_headers[key]

        context = f"[Document: {title} | Type: {media_type}] "
        genres = item.get("genres", [])[:2]
        if genres:
            context += f"Genre: {', '.join(genres)}. "

        self._context_headers[key] = context
        return context

    def _chunk_text(self, text: str, size: int) -> List[str]:
        """Découpage intelligent par phrases sémantiquement cohérentes."""
        import re  # noqa: E402

        sentence_end = re.compile(r"(?<=[.!?])\s+")
        sentences = sentence_end.split(text)

        chunks: List[str] = []
        current_chunk: List[str] = []
        current_length = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if current_length + len(sentence) > size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_length = len(sentence)
            else:
                current_chunk.append(sentence)
                current_length += len(sentence) + 1

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks
