import json
import logging
import os
import re
from typing import Any, List

from adapters.inference.components.context import InferenceComponentContext
from adapters.inference.lazy_load_mixin import LazyLoadMixin
from core.utils.lazy_import import lazy_import
from core.utils.local_models import RERANKER_MODEL
from core.utils.model_registry import get_verified_revision
from core.utils.security import safe_http_request

logger = logging.getLogger("animetix.inference.rerank_component")


class RerankComponent(LazyLoadMixin):
    """Document reranking (Cohere API or local CrossEncoder), composable.

    The single rerank implementation: UnifiedInferenceAdapter and
    LocalRerankAdapter both compose it. ``self._log_usage``/``self.generate``
    are replaced by the injected context. The lazy CrossEncoder cache lives here.
    """

    def __init__(
        self,
        ctx: InferenceComponentContext,
        reranker_model_name: str = RERANKER_MODEL,
    ):
        self._ctx = ctx
        self._reranker_model_name = reranker_model_name
        self._cross_encoder: Any = None

    @property
    def is_loaded(self) -> bool:
        return self._cross_encoder is not None

    def _load_cross_encoder(self) -> None:
        sentence_transformers = lazy_import("sentence_transformers")
        logger.info(f"🏗️ Loading CrossEncoder: {self._reranker_model_name}")
        self._cross_encoder = sentence_transformers.CrossEncoder(
            self._reranker_model_name,
            revision=get_verified_revision(self._reranker_model_name),
        )

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
            # on_error="raise" normalizes a broken load to InferenceError, which
            # this except turns into the prompt/zeros fallback chain.
            self._lazy_load(
                "_cross_encoder",
                self._load_cross_encoder,
                label="CrossEncoder",
                on_error="raise",
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
