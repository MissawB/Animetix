"""Vision Transformers adapter – composes focused mixins for each capability."""
import logging
import aiohttp
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

logger = logging.getLogger("animetix.inference.vision_transformers")


class VisionTransformersAdapter(
    DepthEstimationMixin,
    MangaOcrMixin,
    VideoAnalysisMixin,
    ClipVisionMixin,
    InferencePort,
):
    """Unified vision adapter composing depth, OCR, video, and CLIP capabilities."""

    def __init__(self, use_4bit: bool = True, usage_port: Optional[UsagePort] = None):
        super().__init__(usage_port=usage_port)
        self.use_4bit = use_4bit
        self._http_session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._http_session is None or self._http_session.closed:
            self._http_session = aiohttp.ClientSession()
        return self._http_session

    def detect_objects(self, image_data: bytes, candidate_queries: List[str], model_id: Optional[str] = None) -> List[Dict]:
        try:
            from PIL import Image
            from io import BytesIO
            img = Image.open(BytesIO(image_data)).convert("RGB")
            detector_id = model_id or "google/owlvit-base-patch32"
            if not hasattr(self, '_detector_pipeline') or self._detector_pipeline.model.name_or_path != detector_id:
                self._detector_pipeline = pipeline("zero-shot-object-detection", model=detector_id, device=0 if torch.cuda.is_available() else -1)
            results = self._detector_pipeline(img, candidate_labels=candidate_queries, threshold=0.05)

            self._log_usage(engine=f"transformers:{detector_id}", units=1)

            return [{"label": res["label"], "score": res["score"], "box": [res["box"]["xmin"], res["box"]["ymin"], res["box"]["xmax"], res["box"]["ymax"]]} for res in results]
        except Exception as e:
            logger.error(f"❌ Object Detection failed: {e}")
            return []

    def generate_image_description(self, image_data: bytes, prompt: str = "Décris cette image d'anime.") -> str:
        try:
            from PIL import Image
            from io import BytesIO
            img = Image.open(BytesIO(image_data)).convert("RGB")
            vlm_id = "vikhyatk/moondream2"
            if not hasattr(self, '_vlm_model'):
                self._vlm_tokenizer = AutoTokenizer.from_pretrained(vlm_id)
                self._vlm_model = AutoModelForCausalLM.from_pretrained(vlm_id, trust_remote_code=True).to("cuda" if torch.cuda.is_available() else "cpu")
            enc_image = self._vlm_model.encode_image(img)
            res = self._vlm_model.answer_question(enc_image, prompt, self._vlm_tokenizer)

            self._log_usage(engine=f"transformers:{vlm_id}", units=1)

            return res
        except Exception as e:
            logger.error(f"❌ Image description failed: {e}")
            return "Échec description."

    def health_check(self) -> dict:
        return {"status": "online", "engine": "vision_transformers"}
