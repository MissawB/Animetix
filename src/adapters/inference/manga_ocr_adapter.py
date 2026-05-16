import logging
import json
from typing import List, Dict, Any, Optional
from core.ports.inference_port import InferencePort
from huggingface_hub import InferenceClient

logger = logging.getLogger("animetix.inference.manga_ocr")

class MangaOcrAdapter(InferencePort):
    def __init__(self, token: str = None):
        self.client = InferenceClient(token=token)
        self.primary_model = "rednote-hilab/dots.mocr"
        self.fallback_model = "kha-white/manga-ocr-base"

    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]:
        """
        Processes a manga page using dots.mocr for layout and text.
        """
        try:
            # SOTA 2026: dots.mocr uses a specific document-parsing endpoint
            response = self.client.post(
                data=image_data,
                model=self.primary_model,
                headers={"Content-Type": "image/png"}
            )
            res_data = json.loads(response.decode("utf-8"))
            return {
                "text": res_data.get("generated_text", ""),
                "layout": res_data.get("layout", []),
                "model": "dots.mocr"
            }
        except Exception as e:
            logger.warning(f"dots.mocr failed, falling back to manga-ocr: {e}")
            return self._fallback_manga_ocr(image_data)

    def _fallback_manga_ocr(self, image_data: bytes) -> Dict[str, Any]:
        try:
            response = self.client.post(
                data=image_data,
                model=self.fallback_model,
                headers={"Content-Type": "image/png"}
            )
            res_data = json.loads(response.decode("utf-8"))
            return {
                "text": res_data.get("generated_text", ""),
                "layout": [],
                "model": "manga-ocr"
            }
        except Exception as e:
            logger.error(f"Manga OCR Fallback failed: {e}")
            return {"text": "", "layout": [], "error": str(e)}

    # Stub implementations for required InferencePort methods
    def generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0) -> str: return ""
    def stream_generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0): yield ""
    def calculate_visual_similarity(self, query: str, item_id: str, media_type: str) -> float: return 0.0
    def get_image_embedding(self, image_data: bytes, model_id: Optional[str] = None) -> List[float]: return []
    def classify_image(self, image_data: bytes, candidate_labels: List[str], model_id: Optional[str] = None) -> Dict[str, float]: return {}
    def detect_objects(self, image_data: bytes, candidate_queries: List[str], model_id: Optional[str] = None) -> List[Dict]: return []
    def get_video_temporal_embeddings(self, video_data: bytes) -> List[Dict[str, Any]]: return []
    def localize_video_actions(self, video_data: bytes, action_queries: List[str]) -> List[Dict[str, Any]]: return []
    def transform_image_to_anime(self, image_data: bytes, studio_style: str, prompt: str = "") -> str: return ""
    def transform_video_to_anime(self, video_data: bytes, studio_style: str, prompt: str = "") -> str: return ""
    def generate_soundscape(self, video_metadata: Dict[str, Any], prompt: Optional[str] = None) -> str: return ""
    def clone_voice(self, text: str, reference_audio: bytes, language: str = "fr") -> bytes: return b""
    def speech_to_speech(self, audio_input: bytes, system_prompt: str = "") -> bytes: return b""
    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]: return {"is_safe": True}
    def generate_image_description(self, image_data: bytes, prompt: str = "") -> str: return ""
    def get_diagnostics(self, prompt: str, completion: str) -> Dict[str, Any]: return {}
    def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]: return {}
    def estimate_depth(self, image_data: bytes) -> bytes: return b""
    def generate_3d_scene(self, image_data: bytes, depth_map: bytes) -> Dict[str, Any]: return {}
    def visual_rerank(self, query: str, image_urls: List[str], system_prompt: str = "") -> List[Dict[str, Any]]: return []
    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]: return []
    def inpaint_text_bubbles(self, image_data: bytes, text_placements: List[Dict]) -> str: return ""
    def health_check(self) -> dict: return {"status": "online", "engine": "Manga-OCR"}
