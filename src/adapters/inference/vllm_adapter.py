import requests
import logging
from typing import Optional, List, Dict, Any
from core.ports.inference_port import InferencePort

logger = logging.getLogger("animetix.inference")

class VllmAdapter(InferencePort):
    def __init__(self, api_base: str = "http://localhost:8000/v1", model_name: str = "meta-llama/Llama-3-8B-Instruct"):
        self.api_base = api_base
        self.model_name = model_name

    def generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0) -> str:
        try:
            res = requests.post(f"{self.api_base}/chat/completions", json={
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "thinking_budget": thinking_budget
            }, timeout=30)
            res.raise_for_status()
            return res.json()['choices'][0]['message']['content']
        except requests.exceptions.ConnectionError:
            logger.error(f"vLLM server at {self.api_base} is unreachable.")
        except Exception as e:
            logger.error(f"vLLM Adapter error: {e}")
        return "Erreur: vLLM indisponible."

    def stream_generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0):
        yield self.generate(prompt, system_prompt, thinking_budget)

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
    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]: return {}
    def inpaint_text_bubbles(self, image_data: bytes, text_placements: List[Dict]) -> str: return ""
    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]: return {"is_safe": True}
    def generate_image_description(self, image_data: bytes, prompt: str = "Décris cette image d'anime de manière très détaillée.") -> str:
        """Utilise le VLM pour décrire une image."""
        try:
            # Envoi via l'API vLLM (multimodal support)
            res = requests.post(f"{self.api_base}/chat/completions", json={
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + image_data.hex()}} # Placeholder for base64
                    ]}
                ]
            }, timeout=30)
            res.raise_for_status()
            return res.json()['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"VLM Image Description error: {e}")
            return "Impossible de décrire l'image."

    def get_diagnostics(self, prompt: str, completion: str) -> Dict[str, Any]: return {}
    def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]: return {}
    def estimate_depth(self, image_data: bytes) -> bytes: return b""
    def generate_3d_scene(self, image_data: bytes, depth_map: bytes) -> Dict[str, Any]: return {}
    
    def visual_rerank(self, query: str, image_urls: List[str], system_prompt: str = "") -> List[Dict[str, Any]]:
        return [{"url": url, "score": 1.0} for url in image_urls]
        
    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]:
        return []

    def health_check(self) -> dict:
        try:
            res = requests.get(f"{self.api_base}/models", timeout=5)
            if res.status_code == 200: return {"status": "online", "engine": "vLLM", "model": self.model_name}
        except Exception as e:
            logger.error(f"vLLM health check failed: {e}")
        return {"status": "offline", "engine": "vLLM"}
