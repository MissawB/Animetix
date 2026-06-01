"""Vision Transformers adapter – composes focused mixins for each capability."""
import logging
import httpx
from typing import Optional, List, Dict, Any
from core.ports.inference_port import InferencePort
from core.ports.usage_port import UsagePort
from core.domain.exceptions import InferenceError
from core.utils.lazy_import import lazy_import

# Mixin imports
from adapters.inference.depth_estimation import DepthEstimationMixin
from adapters.inference.manga_ocr import MangaOcrMixin
from adapters.inference.video_analysis import VideoAnalysisMixin
from adapters.inference.clip_vision import ClipVisionMixin

torch = lazy_import('torch')
transformers = lazy_import('transformers')
AutoModelForCausalLM = transformers.AutoModelForCausalLM
AutoTokenizer = transformers.AutoTokenizer
pipeline = transformers.pipeline

from adapters.inference.vlm_mixin import VlmMixin

logger = logging.getLogger("animetix.inference.vision_transformers")


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

    def health_check(self) -> dict:
        return {"status": "online", "engine": "vision_transformers"}
