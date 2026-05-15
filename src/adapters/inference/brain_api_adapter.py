import os
import requests
import time
from typing import Optional, List, Dict, Any
from core.ports.inference_port import InferencePort

class BrainAPIAdapter(InferencePort):
    def __init__(self, brain_api_url: str, max_retries: int = 3):
        self.brain_api_url = brain_api_url
        self.max_retries = max_retries

    def generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0) -> str:
        if not self.brain_api_url: return "Erreur: BRAIN_API_URL non configurée."
        for _ in range(self.max_retries):
            try:
                res = requests.post(f"{self.brain_api_url}/generate", json={
                    "prompt": prompt, 
                    "system_prompt": system_prompt,
                    "thinking_budget": thinking_budget
                }, timeout=30)
                if res.status_code == 200: return res.json().get("text", "")
            except: time.sleep(1)
        return "Erreur: Le cerveau distant ne répond pas."

    def stream_generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0):
        # Implementation of streaming depends on brain_api capability
        yield self.generate(prompt, system_prompt, thinking_budget)

    def calculate_visual_similarity(self, query: str, item_id: str, media_type: str) -> float:
        if not self.brain_api_url: return 0.0
        try:
            res = requests.post(f"{self.brain_api_url}/similarity/visual", json={"query": query, "item_id": item_id, "media_type": media_type}, timeout=10)
            if res.status_code == 200: return res.json().get("score", 0.0)
        except: pass
        return 0.0

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
    def generate_image_description(self, image_data: bytes, prompt: str = "") -> str: return ""
    def get_diagnostics(self, prompt: str, completion: str) -> Dict[str, Any]: return {}
    def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]: return {}
    def estimate_depth(self, image_data: bytes) -> bytes: return b""
    def generate_3d_scene(self, image_data: bytes, depth_map: bytes) -> Dict[str, Any]: return {}
    
    def visual_rerank(self, query: str, image_urls: List[str], system_prompt: str = "") -> List[Dict[str, Any]]:
        return [{"url": url, "score": 1.0} for url in image_urls]
        
    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]:
        return []

    def health_check(self) -> dict:
        if not self.brain_api_url: return {"status": "offline", "reason": "No URL"}
        try:
            res = requests.get(f"{self.brain_api_url}/health", timeout=5)
            if res.status_code == 200: return {"status": "online", "engine": "Brain-API"}
        except: pass
        return {"status": "offline", "engine": "Brain-API"}
