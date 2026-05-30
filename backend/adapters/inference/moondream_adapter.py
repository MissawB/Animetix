import logging
from typing import Optional, List, Dict, Any
from core.ports.inference_port import InferencePort, InferenceNotImplementedError
from core.ports.usage_port import UsagePort
from core.utils.lazy_import import lazy_import
from core.domain.exceptions import InferenceError

torch = lazy_import('torch')

logger = logging.getLogger("animetix.inference")

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
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_id, trust_remote_code=True)
        except Exception as e:
            logger.error(f"Failed to load Moondream model {self.model_id}: {e}")
            raise InferenceError(f"Failed to load Moondream model: {e}")

    def generate_image_description(self, image_data: bytes, prompt: str = "Décris cette image d'anime de manière très détaillée.") -> str:
        self._load_model()
        if not self.model or not self.tokenizer:
            raise InferenceError("Moondream model or tokenizer not loaded.")

        import io
        from PIL import Image

        try:
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            enc_image = self.model.encode_image(image)
            description = self.model.answer_question(enc_image, prompt, self.tokenizer)
            self._log_usage(engine="local:moondream", units=1)
            return description
        except Exception as e:
            logger.error(f"Moondream visual description failed: {e}")
            raise InferenceError(f"Moondream visual description failed: {e}")

    def health_check(self) -> dict:
        return {"status": "online" if self.model else "offline", "engine": "Moondream-VLM"}
