import logging
from typing import Optional, List
from core.ports.inference_port import InferencePort
from core.domain.exceptions import InferenceError
from core.domain.entities.ai_schemas import InferenceResponse
from core.utils.lazy_import import lazy_import

torch = lazy_import("torch")
transformers = lazy_import("transformers")

from core.ports.usage_port import UsagePort  # noqa: E402

logger = logging.getLogger("animetix.inference.text")


class LocalTextAdapter(InferencePort):
    def __init__(
        self,
        model_id: str = "Qwen/Qwen3.5-4B",
        use_4bit: bool = True,
        usage_port: Optional[UsagePort] = None,
    ):
        super().__init__(usage_port=usage_port)
        self.model_id = model_id
        self.model = None
        self.tokenizer = None
        self._embedding_model = None
        self.use_4bit = use_4bit

    def _load_model(self):
        if self.model:
            return
        try:
            from transformers import (
                BitsAndBytesConfig,
                AutoModelForCausalLM,
                AutoTokenizer,
            )  # noqa: E402

            logger.info(f"🏗️ Loading Local Text Model: {self.model_id}")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_id, revision="main"
            )  # nosec B615
            quantization_config = (
                BitsAndBytesConfig(load_in_4bit=True) if self.use_4bit else None
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                revision="main",
                device_map="auto",
                quantization_config=quantization_config,
                trust_remote_code=True,
            )  # nosec B615
        except Exception as e:
            logger.error(f"❌ Failed to load local text model: {e}")
            raise InferenceError(
                f"Critical failure during text model loading: {str(e)}"
            )

    def generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs,
    ) -> InferenceResponse:
        self._load_model()
        try:
            if thinking_mode or thinking_budget > 0:
                prompt = f"<think>\nAnalyse en profondeur.\n</think>\n{prompt}"
            inputs = self.tokenizer(
                f"{system_prompt}\n\n{prompt}", return_tensors="pt"
            ).to(self.model.device)
            input_length = inputs.input_ids.shape[1]
            outputs = self.model.generate(
                **inputs, max_new_tokens=512 + thinking_budget
            )

            output_tokens = outputs[0][input_length:]
            text = self.tokenizer.decode(
                output_tokens, skip_special_tokens=True
            ).strip()

            self._log_usage(
                engine=f"local:{self.model_id}",
                input_tokens=input_length,
                output_tokens=len(output_tokens),
                allocated_budget=thinking_budget,
            )

            return InferenceResponse(text=text)
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise InferenceError(f"Text generation failed: {str(e)}")

    def stream_generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs,
    ):
        yield self.generate(
            prompt, system_prompt, thinking_budget, thinking_mode, include_logprobs
        )

    def get_text_embedding(self, text: str) -> List[float]:
        """Génère un embedding local via SentenceTransformer."""
        if not self._embedding_model:
            from sentence_transformers import SentenceTransformer  # noqa: E402

            logger.info("🏗️ Loading Local Embedding Model: all-MiniLM-L6-v2")
            self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

        embedding = self._embedding_model.encode(text)

        self._log_usage(engine="local:all-MiniLM-L6-v2", units=1)

        return embedding.tolist()

    def health_check(self) -> dict:
        return {
            "status": "online" if self.model or self._embedding_model else "offline",
            "engine": "local_text",
        }
