import logging
import os
from typing import List, Optional
from core.ports.inference_port import InferencePort
from core.domain.exceptions import InferenceError
from core.ports.usage_port import UsagePort

logger = logging.getLogger("animetix.inference.rerank")

class LocalRerankAdapter(InferencePort):
    def __init__(self, model_name: Optional[str] = None, usage_port: Optional[UsagePort] = None):
        super().__init__(usage_port=usage_port)
        self.model_name = model_name or os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
        self._cross_encoder = None

    def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
        if not documents:
            return []
            
        cohere_key = os.getenv("COHERE_API_KEY")
        if cohere_key:
            try:
                import httpx
                headers = {
                    "Authorization": f"Bearer {cohere_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "rerank-multilingual-v3.0",
                    "query": query,
                    "documents": documents
                }
                response = httpx.post("https://api.cohere.ai/v1/rerank", headers=headers, json=payload, timeout=10, follow_redirects=True)
                if response.status_code == 200:
                    data = response.json()
                    scores = [0.0] * len(documents)
                    for item in data.get("results", []):
                        idx = item.get("index")
                        if idx is not None and idx < len(scores):
                            scores[idx] = float(item.get("relevance_score", 0.0))
                    self._log_usage(engine="cohere:rerank", units=len(documents))
                    return scores
            except Exception as e:
                logger.error(f"⚠️ Cohere Rerank API connection failed: {e}.")

        try:
            from core.utils.lazy_import import lazy_import
            sentence_transformers = lazy_import('sentence_transformers')
            
            if not self._cross_encoder:
                logger.info(f"🏗️ Loading CrossEncoder Model: {self.model_name}")
                self._cross_encoder = sentence_transformers.CrossEncoder(self.model_name)
                
            pairs = [[query, doc] for doc in documents]
            scores = self._cross_encoder.predict(pairs)
            self._log_usage(engine="local:rerank", units=len(documents))
            return [float(score) for score in scores]
        except Exception as e:
            logger.error(f"❌ Failed to run local reranker: {e}")
            raise InferenceError(f"Reranking failed: {str(e)}")

    def health_check(self) -> dict:
        return {"status": "online" if self._cross_encoder else "offline", "engine": "local_rerank"}
