import logging
from typing import List, Dict, Any, Optional
from core.ports.inference_port import InferencePort, InferenceNotImplementedError
from core.ports.usage_port import UsagePort
from core.utils.lazy_import import lazy_import

torch = lazy_import('torch')
transformers = lazy_import('transformers')

logger = logging.getLogger("animetix.inference.transformers_text")

class TransformersTextAdapter(InferencePort):
    """
    Real implementation of TransformersTextAdapter using Hugging Face transformers.
    Supports text generation and embeddings.
    """

    def __init__(self, model_id: str = "Qwen/Qwen2.5-1.5B-Instruct", use_4bit: bool = True, usage_port: Optional[UsagePort] = None) -> None:
        super().__init__(usage_port=usage_port)
        self.model_id = model_id
        self.use_4bit = use_4bit
        self._pipeline = None
        self._embedding_model = None

    def _load_generation_pipeline(self):
        if self._pipeline: return
        try:
            logger.info(f"🏗️ Loading Transformers Text Model: {self.model_id}")
            
            # Using pipeline for simplicity
            self._pipeline = transformers.pipeline(
                "text-generation",
                model=self.model_id,
                device_map="auto",
                model_kwargs={"load_in_4bit": self.use_4bit} if self.use_4bit and torch.cuda.is_available() else {}
            )
        except Exception as e:
            logger.error(f"❌ Failed to load transformers model {self.model_id}: {e}")
            raise

    def generate(self, prompt: str, system_prompt: str = "Tu es un expert en Anime.", thinking_budget: int = 0, thinking_mode: bool = False) -> str:
        try:
            self._load_generation_pipeline()
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            # Handle thinking mode via prompt injection if supported/requested
            if thinking_mode or thinking_budget > 0:
                messages[0]["content"] += "\n<think>\nAnalyse la requête en profondeur.\n</think>"

            outputs = self._pipeline(
                messages,
                max_new_tokens=512 + thinking_budget,
                do_sample=True,
                temperature=0.7,
                top_p=0.9
            )
            
            result = outputs[0]["generated_text"][-1]["content"]
            
            # Log usage (heuristic)
            self._log_usage(
                engine=f"transformers:{self.model_id}",
                input_tokens=len(prompt) // 4,
                output_tokens=len(result) // 4
            )
            
            return result
        except Exception as e:
            logger.error(f"Transformers Generation Error: {e}")
            return f"Erreur Transformers: {e}"

    def stream_generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False):
        # Transformers pipeline doesn't support streaming easily in this one-liner way.
        # Fallback to full generation for now.
        yield self.generate(prompt, system_prompt, thinking_budget, thinking_mode)

    def get_text_embedding(self, text: str) -> List[float]:
        try:
            if not self._embedding_model:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            
            emb = self._embedding_model.encode(text).tolist()
            self._log_usage(engine="transformers:embedding", units=1)
            return emb
        except Exception as e:
            logger.error(f"Transformers Embedding Error: {e}")
            return []

    def health_check(self) -> dict:
        return {
            "status": "online" if self._pipeline else "offline", 
            "engine": "transformers_local",
            "model": self.model_id
        }

    # Other methods remain as stubs or raising error
    def calculate_visual_similarity(self, query: str, item_id: str, media_type: str) -> float:
        raise InferenceNotImplementedError("Visual tasks not supported by Text adapter.")

    def get_image_embedding(self, image_data: bytes, model_id: Optional[str] = None) -> List[float]:
        raise InferenceNotImplementedError()

    def classify_image(self, image_data: bytes, candidate_labels: List[str], model_id: Optional[str] = None) -> Dict[str, float]:
        raise InferenceNotImplementedError()

    def generate_image_description(self, image_data: bytes, prompt: str = "") -> str:
        raise InferenceNotImplementedError()

    def visual_rerank(self, query: str, image_urls: List[str], system_prompt: str = "") -> List[Dict[str, Any]]:
        raise InferenceNotImplementedError()

    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]:
        raise InferenceNotImplementedError()

    def generate_image(self, prompt: str, style: str = "") -> str:
        raise InferenceNotImplementedError()
