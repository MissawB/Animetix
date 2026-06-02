import logging
import os
from typing import List, Optional
from core.ports.inference_port import InferencePort
from core.domain.exceptions import InferenceError
from core.ports.usage_port import UsagePort

from core.utils.security import safe_http_request

from adapters.inference.rerank_mixin import RerankMixin

logger = logging.getLogger("animetix.inference.rerank")

class LocalRerankAdapter(RerankMixin, InferencePort):
    def __init__(self, model_name: Optional[str] = None, usage_port: Optional[UsagePort] = None):
        super().__init__(usage_port=usage_port)
        self.reranker_model_name = model_name or os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.model_name = self.reranker_model_name
        self._cross_encoder = None

    def health_check(self) -> dict:
        return {"status": "online" if self._cross_encoder else "offline", "engine": "local_rerank"}
