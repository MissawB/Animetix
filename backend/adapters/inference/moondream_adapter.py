import logging
from typing import Optional, List, Dict, Any
from core.ports.inference_port import InferencePort, InferenceNotImplementedError
from core.ports.usage_port import UsagePort
from core.domain.entities.ai_schemas import InferenceResponse
from core.utils.lazy_import import lazy_import
from core.domain.exceptions import InferenceError

torch = lazy_import('torch')
transformers = lazy_import('transformers')
PIL = lazy_import('PIL.Image')

logger = logging.getLogger("animetix.inference.moondream")

class MoondreamAdapter(InferencePort):
    def __init__(self, model_id: str = "vikhyatk/moondream2", usage_port: Optional[UsagePort] = None):
        super().__init__(usage_port=usage_port)
        self.model_id = model_id
        self.model = None
        self.tokenizer = None

    def _load_model(self):
        if self.model: return
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            self.model = AutoModelForCausalLM.from_pretrained(self.model_id, trust_remote_code=True, device_map="auto")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        except Exception as e:
            logger.error(f"Failed to load Moondream model: {e}")
            raise InferenceError(f"Moondream loading failed: {e}")

    def generate(
        self, 
        prompt: str, 
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.", 
        thinking_budget: int = 0, 
        thinking_mode: bool = False, 
        include_logprobs: bool = False,
        **kwargs
    ) -> InferenceResponse:
        raise InferenceNotImplementedError("Pure text generation not supported by MoondreamAdapter")

    def stream_generate(
        self, 
        prompt: str, 
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.", 
        thinking_budget: int = 0, 
        thinking_mode: bool = False, 
        include_logprobs: bool = False,
        **kwargs
    ):
        raise InferenceNotImplementedError("Streaming generation not supported by MoondreamAdapter")

    def get_text_embedding(self, text: str) -> List[float]:
        raise InferenceNotImplementedError("Text embedding not supported by MoondreamAdapter")

    def generate_image_description(self, image_data: bytes, prompt: str = "Décris cette image d'anime de manière très détaillée.") -> str:
        self._load_model()
        try:
            import io
            from PIL import Image
            image = Image.open(io.BytesIO(image_data))
            enc_image = self.model.encode_image(image)
            description = self.model.answer_question(enc_image, prompt, self.tokenizer)
            
            self._log_usage(engine="local:moondream2", units=1)
            return description
        except Exception as e:
            logger.error(f"Moondream visual description failed: {e}")
            raise InferenceError(f"Moondream visual description failed: {e}")

    def health_check(self) -> dict:
        return {"status": "online" if self.model else "offline", "engine": "Moondream-VLM"}
