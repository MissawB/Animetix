"""Vision Transformers adapter – composes focused mixins for each capability."""

import logging  # noqa: E402
from typing import List, Optional  # noqa: E402

import httpx  # noqa: E402
from adapters.inference.lazy_local_model_adapter import (
    LazyLocalModelAdapter,  # noqa: E402
)
from core.domain.entities.ai_schemas import InferenceResponse  # noqa: E402
from core.ports.inference_port import InferenceNotImplementedError  # noqa: E402
from core.ports.usage_port import UsagePort  # noqa: E402

from .clip_vision import ClipVisionMixin  # noqa: E402
from .depth_estimation import DepthEstimationMixin  # noqa: E402
from .manga_ocr import MangaOcrMixin  # noqa: E402
from .video_analysis import VideoAnalysisMixin  # noqa: E402

# Capability mixins
from .vlm_mixin import VlmMixin  # noqa: E402

logger = logging.getLogger("animetix.inference.vision")


class VisionTransformersAdapter(
    DepthEstimationMixin,
    MangaOcrMixin,
    VideoAnalysisMixin,
    ClipVisionMixin,
    VlmMixin,
    LazyLocalModelAdapter,
):
    """Unified vision adapter composing depth, OCR, video, and CLIP capabilities."""

    ENGINE_NAME = "vision_transformers"

    def _is_ready(self) -> bool:
        # Multi-capability lazy facade: each mixin loads its sub-model on demand,
        # so the facade is "available" as soon as it is constructed.
        return True

    def __init__(self, use_4bit: bool = True, usage_port: Optional[UsagePort] = None):
        super().__init__(usage_port=usage_port)
        self.use_4bit = use_4bit
        self._http_client: Optional[httpx.AsyncClient] = None

    def generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs,
    ) -> InferenceResponse:
        raise InferenceNotImplementedError(
            "Text generation not supported by VisionTransformersAdapter"
        )

    def stream_generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs,
    ):
        raise InferenceNotImplementedError(
            "Streaming generation not supported by VisionTransformersAdapter"
        )

    def get_text_embedding(self, text: str) -> List[float]:
        raise InferenceNotImplementedError(
            "Text embedding not supported by VisionTransformersAdapter"
        )
