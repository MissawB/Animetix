import json
import logging
import os
import re
from typing import Any, List

from adapters.inference.components.context import InferenceComponentContext
from core.utils.lazy_import import lazy_import
from core.utils.security import safe_http_request

logger = logging.getLogger("animetix.inference.rerank_component")

DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-12-v2"


class RerankComponent:
    """Document reranking (Cohere API or local CrossEncoder), composable.

    Logic copied verbatim from RerankMixin; ``self._log_usage``/``self.generate``
    are replaced by the injected context. The lazy CrossEncoder cache lives here.
    """

    def __init__(
        self,
        ctx: InferenceComponentContext,
        reranker_model_name: str = DEFAULT_RERANKER_MODEL,
    ):
        self._ctx = ctx
        self._reranker_model_name = reranker_model_name
        self._cross_encoder: Any = None

    @property
    def is_loaded(self) -> bool:
        return self._cross_encoder is not None

    def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
        if not documents:
            return []

        cohere_key = os.getenv("COHERE_API_KEY")
        if cohere_key:
            try:
                headers = {
                    "Authorization": f"Bearer {cohere_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": "rerank-multilingual-v3.0",
                    "query": query,
                    "documents": documents,
                }
                response = safe_http_request(
                    "POST",
                    "https://api.cohere.ai/v1/rerank",
                    headers=headers,
                    json=payload,
                    timeout=10,
                )
                if response.status_code == 200:
                    data = response.json()
                    scores = [0.0] * len(documents)
                    for item in data.get("results", []):
                        idx = item.get("index")
                        if idx is not None and idx < len(scores):
                            scores[idx] = float(item.get("relevance_score", 0.0))
                    self._ctx.log_usage(engine="cohere:rerank", units=len(documents))
                    return scores
            except Exception as e:
                logger.warning(
                    f"⚠️ Cohere Rerank API failed: {e}. Falling back to local/prompt."
                )

        try:
            sentence_transformers = lazy_import("sentence_transformers")
            if self._cross_encoder is None:
                logger.info(f"🏗️ Loading CrossEncoder: {self._reranker_model_name}")
                self._cross_encoder = sentence_transformers.CrossEncoder(
                    self._reranker_model_name
                )
            pairs = [[query, doc] for doc in documents]
            scores = self._cross_encoder.predict(pairs)
            self._ctx.log_usage(engine="local:rerank", units=len(documents))
            return [float(score) for score in scores]
        except Exception as e:
            logger.error(f"❌ Local reranker failed: {e}")
            if self._ctx.generate is not None:
                logger.info("Using prompt-based reranking fallback.")
                prompt = f"Requête: {query}\n\nDocuments à évaluer:\n"
                for i, doc in enumerate(documents):
                    prompt += f"ID {i}: {doc[:500]}\n"
                prompt += "\nDonne un score de pertinence entre 0.0 et 1.0 pour chaque document. Réponds avec une liste JSON: [score0, score1, ...]"
                try:
                    raw = self._ctx.generate(
                        prompt, system_prompt="Tu es un reranker expert."
                    )
                    match = re.search(r"\[.*\]", raw)
                    if match:
                        scores = json.loads(match.group(0))
                        if len(scores) == len(documents):
                            return [float(s) for s in scores]
                except Exception as e:
                    logger.warning(f"Prompt-based reranking fallback failed: {e}")
            return [0.0] * len(documents)
