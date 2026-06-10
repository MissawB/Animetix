"""Vision Transformers adapter – composes focused mixins for each capability."""
import logging
import httpx
from typing import Optional, List, Dict, Any
from core.ports.inference_port import InferencePort, InferenceNotImplementedError
from core.ports.usage_port import UsagePort
from core.domain.entities.ai_schemas import InferenceResponse

# Capability mixins
from .vlm_mixin import VlmMixin
from .video_analysis import VideoAnalysisMixin
from .manga_ocr import MangaOcrMixin
from .depth_estimation import DepthEstimationMixin
from .clip_vision import ClipVisionMixin

logger = logging.getLogger("animetix.inference.vision")

class VisionTransformersAdapter(
    DepthEstimationMixin,
    MangaOcrMixin,
    VideoAnalysisMixin,
    ClipVisionMixin,
    VlmMixin,
    InferencePort,
):
    """Unified vision adapter composing depth, OCR, video, and CLIP capabilities."""

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
        **kwargs
    ) -> InferenceResponse:
        raise InferenceNotImplementedError("Text generation not supported by VisionTransformersAdapter")

    def stream_generate(
        self, 
        prompt: str, 
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.", 
        thinking_budget: int = 0, 
        thinking_mode: bool = False, 
        include_logprobs: bool = False,
        **kwargs
    ):
        raise InferenceNotImplementedError("Streaming generation not supported by VisionTransformersAdapter")

    def get_text_embedding(self, text: str) -> List[float]:
        raise InferenceNotImplementedError("Text embedding not supported by VisionTransformersAdapter")

    def health_check(self) -> dict:
        return {"status": "online", "engine": "vision_transformers"}
