from typing import List, Optional, Dict, Any
import logging
from core.ports.inference_port import InferencePort

logger = logging.getLogger('animetix')

class FallbackInferenceAdapter(InferencePort):
    def __init__(self, adapters: List[InferencePort]):
        self.adapters = [a for a in adapters if a is not None]

    def _fallback_call(self, method_name: str, *args, **kwargs):
        last_error = ""
        for adapter in self.adapters:
            try:
                method = getattr(adapter, method_name)
                res = method(*args, **kwargs)
                if res: return res
            except Exception as e:
                last_error = str(e)
                continue
        return None

    def generate(self, prompt: str, system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.", thinking_budget: int = 0) -> str:
        last_error = ""
        for adapter in self.adapters:
            try:
                result = adapter.generate(prompt, system_prompt, thinking_budget)
                if result and not result.startswith("Erreur"): return result
                last_error = result
            except Exception as e:
                last_error = str(e)
                continue
        return f"Échec critique : Tous les moteurs LLM ont échoué. Dernière erreur: {last_error}"

    def stream_generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0):
        for adapter in self.adapters:
            try:
                return adapter.stream_generate(prompt, system_prompt, thinking_budget)
            except:
                continue
        def error_gen(): yield self.generate(prompt, system_prompt, thinking_budget)
        return error_gen()

    def calculate_visual_similarity(self, query: str, item_id: str, media_type: str) -> float:
        res = self._fallback_call("calculate_visual_similarity", query, item_id, media_type)
        return float(res) if res is not None else 0.0

    def get_image_embedding(self, image_data: bytes, model_id: Optional[str] = None) -> List[float]:
        return self._fallback_call("get_image_embedding", image_data, model_id) or []

    def classify_image(self, image_data: bytes, candidate_labels: List[str], model_id: Optional[str] = None) -> Dict[str, float]:
        return self._fallback_call("classify_image", image_data, candidate_labels, model_id) or {}

    def detect_objects(self, image_data: bytes, candidate_queries: List[str], model_id: Optional[str] = None) -> List[Dict]:
        return self._fallback_call("detect_objects", image_data, candidate_queries, model_id) or []

    def get_video_temporal_embeddings(self, video_data: bytes) -> List[Dict[str, Any]]:
        return self._fallback_call("get_video_temporal_embeddings", video_data) or []

    def localize_video_actions(self, video_data: bytes, action_queries: List[str]) -> List[Dict[str, Any]]:
        return self._fallback_call("localize_video_actions", video_data, action_queries) or []

    def transform_image_to_anime(self, image_data: bytes, studio_style: str, prompt: str = "") -> str:
        return self._fallback_call("transform_image_to_anime", image_data, studio_style, prompt) or ""

    def transform_video_to_anime(self, video_data: bytes, studio_style: str, prompt: str = "") -> str:
        return self._fallback_call("transform_video_to_anime", video_data, studio_style, prompt) or ""

    def generate_soundscape(self, video_metadata: Dict[str, Any], prompt: Optional[str] = None) -> str:
        return self._fallback_call("generate_soundscape", video_metadata, prompt) or ""

    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]:
        return self._fallback_call("process_manga_page", image_data) or {}

    def inpaint_text_bubbles(self, image_data: bytes, text_placements: List[Dict]) -> str:
        return self._fallback_call("inpaint_text_bubbles", image_data, text_placements) or ""

    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        return self._fallback_call("moderate_content", text, categories) or {}

    def generate_image_description(self, image_data: bytes, prompt: str = "") -> str:
        return self._fallback_call("generate_image_description", image_data, prompt) or ""

    def get_diagnostics(self, prompt: str, completion: str) -> Dict[str, Any]:
        return self._fallback_call("get_diagnostics", prompt, completion) or {}

    def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]:
        return self._fallback_call("calculate_uncertainty", prompt, completion) or {}

    def clone_voice(self, text: str, reference_audio: bytes, language: str = "fr") -> bytes:
        return self._fallback_call("clone_voice", text, reference_audio, language) or b""

    def speech_to_speech(self, audio_input: bytes, system_prompt: str = "") -> bytes:
        return self._fallback_call("speech_to_speech", audio_input, system_prompt) or b""

    def estimate_depth(self, image_data: bytes) -> bytes:
        return self._fallback_call("estimate_depth", image_data) or b""

    def generate_3d_scene(self, image_data: bytes, depth_map: bytes) -> Dict[str, Any]:
        return self._fallback_call("generate_3d_scene", image_data, depth_map) or {}

    def visual_rerank(self, query: str, image_urls: List[str], system_prompt: str = "") -> List[Dict[str, Any]]:
        return self._fallback_call("visual_rerank", query, image_urls, system_prompt) or []

    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]:
        return self._fallback_call("get_multimodal_late_interaction", image_data) or []

    def health_check(self) -> dict:
        statuses = [a.health_check() for a in self.adapters]
        is_online = any(s.get("status") == "online" for s in statuses)
        return {"status": "online" if is_online else "offline", "adapters": statuses}
