"""Reranking mixin for Inference adapters."""

import logging  # noqa: E402
import os  # noqa: E402
from typing import List  # noqa: E402

from core.utils.lazy_import import lazy_import  # noqa: E402
from core.utils.security import safe_http_request  # noqa: E402

logger = logging.getLogger("animetix.inference.rerank_mixin")


class RerankMixin:
    """Provides document reranking capabilities (Cohere API or local Cross-Encoder)."""

    def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
        """Évalue la pertinence de plusieurs documents par rapport à une requête."""
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
                    self._log_usage(engine="cohere:rerank", units=len(documents))
                    return scores
            except Exception as e:
                logger.warning(
                    f"⚠️ Cohere Rerank API failed: {e}. Falling back to local/prompt."
                )

        try:
            sentence_transformers = lazy_import("sentence_transformers")
            model_name = getattr(
                self, "reranker_model_name", "cross-encoder/ms-marco-MiniLM-L-12-v2"
            )

            if not hasattr(self, "_cross_encoder") or self._cross_encoder is None:
                logger.info(f"🏗️ Loading CrossEncoder: {model_name}")
                self._cross_encoder = sentence_transformers.CrossEncoder(model_name)

            pairs = [[query, doc] for doc in documents]
            scores = self._cross_encoder.predict(pairs)
            self._log_usage(engine="local:rerank", units=len(documents))
            return [float(score) for score in scores]
        except Exception as e:
            logger.error(f"❌ Local reranker failed: {e}")

            # Prompt-based fallback if LLM is available (for UnifiedInferenceAdapter)
            if hasattr(self, "generate"):
                logger.info("Using prompt-based reranking fallback.")
                prompt = f"Requête: {query}\n\nDocuments à évaluer:\n"
                for i, doc in enumerate(documents):
                    prompt += f"ID {i}: {doc[:500]}\n"
                prompt += "\nDonne un score de pertinence entre 0.0 et 1.0 pour chaque document. Réponds avec une liste JSON: [score0, score1, ...]"
                try:
                    import json  # noqa: E402
                    import re  # noqa: E402

                    raw = self.generate(
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
