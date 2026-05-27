from typing import List, Dict, Any, Optional

from core.ports.inference_port import InferencePort, InferenceNotImplementedError


class TransformersTextAdapter(InferencePort):
    """A minimal stub adapter for text‑only transformer models.
    The real implementation would wrap a HuggingFace transformer for tasks such as
    text generation, classification or embedding. For now we provide safe fallback
    methods so the test suite can import the class without raising errors.
    """

    def __init__(self, model_name: str = "distilbert-base-uncased") -> None:
        self.model_name = model_name
        self.model = None  # Placeholder for an actual model instance

    def _load_model(self) -> None:
        # In a full implementation we would load the transformer here.
        # For the stub we simply note that the model is not loaded.
        if self.model is None:
            # No heavy imports to keep the stub lightweight.
            pass

    def generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False) -> str:
        # Text generation not implemented in the stub.
        # TODO: implement generate for TransformersTextAdapter
        pass

    def stream_generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False):
        # Streaming generation not implemented.
        # TODO: implement stream_generate for TransformersTextAdapter
        pass

    def calculate_visual_similarity(self, query: str, item_id: str, media_type: str) -> float:
        # TODO: implement calculate_visual_similarity method for this adapter
        pass

    def get_image_embedding(self, image_data: bytes, model_id: Optional[str] = None) -> List[float]:
        # TODO: implement get_image_embedding method for this adapter
        pass

    def classify_image(self, image_data: bytes, candidate_labels: List[str], model_id: Optional[str] = None) -> Dict[str, float]:
        # TODO: implement classify_image method for this adapter
        pass

    def generate_image_description(self, image_data: bytes, prompt: str = "") -> str:
        # TODO: implement generate_image_description method for this adapter
        pass

    def visual_rerank(self, query: str, image_urls: List[str], system_prompt: str = "") -> List[Dict[str, Any]]:
        # TODO: implement visual_rerank method for this adapter
        pass

    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]:
        # TODO: implement get_multimodal_late_interaction method for this adapter
        pass

    def generate_image(self, prompt: str, style: str = "") -> str:
        # TODO: implement generate_image method for this adapter
        pass

    def health_check(self) -> dict:
        return {"status": "offline", "engine": "transformers_text_stub"}
