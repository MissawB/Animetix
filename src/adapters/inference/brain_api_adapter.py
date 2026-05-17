import os
import requests
import time
import logging
from typing import Optional, List, Dict, Any
from core.ports.inference_port import InferencePort

logger = logging.getLogger("animetix.inference")

class BrainAPIAdapter(InferencePort):
    def __init__(self, brain_api_url: str, max_retries: int = 3):
        self.brain_api_url = brain_api_url
        self.max_retries = max_retries

    def generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False) -> str:
        if not self.brain_api_url: return "Erreur: BRAIN_API_URL non configurée."
        for attempt in range(self.max_retries):
            try:
                res = requests.post(f"{self.brain_api_url}/generate", json={
                    "prompt": prompt, 
                    "system_prompt": system_prompt,
                    "thinking_budget": thinking_budget,
                    "thinking_mode": thinking_mode
                }, timeout=30)
                res.raise_for_status()
                return res.json().get("text", "")
            except requests.exceptions.RequestException as e:
                logger.error(f"BrainAPI Request failed (Attempt {attempt+1}/{self.max_retries}): {e}")
                time.sleep(1)
            except Exception as e:
                logger.error(f"Unexpected BrainAPI error: {e}")
                break
        return "Erreur: Le cerveau distant ne répond pas."

    def stream_generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False):
        # Implementation of streaming depends on brain_api capability
        yield self.generate(prompt, system_prompt, thinking_budget, thinking_mode)

    def calculate_visual_similarity(self, query: str, item_id: str, media_type: str) -> float:
        if not self.brain_api_url: return 0.0
        try:
            res = requests.post(f"{self.brain_api_url}/similarity/visual", json={"query": query, "item_id": item_id, "media_type": media_type}, timeout=10)
            if res.status_code == 200: return res.json().get("score", 0.0)
        except Exception as e:
            logger.error(f"BrainAPI Visual Similarity error: {e}")
        return 0.0

    def get_image_embedding(self, image_data: bytes, model_id: Optional[str] = None) -> List[float]: raise NotImplementedError("get_image_embedding non implémentée")
    def classify_image(self, image_data: bytes, candidate_labels: List[str], model_id: Optional[str] = None) -> Dict[str, float]: raise NotImplementedError("classify_image non implémentée")
    def detect_objects(self, image_data: bytes, candidate_queries: List[str], model_id: Optional[str] = None) -> List[Dict]: raise NotImplementedError("detect_objects non implémentée")
    def get_video_temporal_embeddings(self, video_data: bytes) -> List[Dict[str, Any]]: raise NotImplementedError("get_video_temporal_embeddings non implémentée")
    def localize_video_actions(self, video_data: bytes, action_queries: List[str]) -> List[Dict[str, Any]]: raise NotImplementedError("localize_video_actions non implémentée")
    def transform_image_to_anime(self, image_data: bytes, studio_style: str, prompt: str = "") -> str: raise NotImplementedError("transform_image_to_anime non implémentée")
    def transform_video_to_anime(self, video_data: bytes, studio_style: str, prompt: str = "") -> str: raise NotImplementedError("transform_video_to_anime non implémentée")
    def generate_soundscape(self, video_metadata: Dict[str, Any], prompt: Optional[str] = None) -> str: raise NotImplementedError("generate_soundscape non implémentée")
    def clone_voice(self, text: str, reference_audio: bytes, language: str = "fr") -> bytes: raise NotImplementedError("clone_voice non implémentée")
    def speech_to_speech(self, audio_input: bytes, system_prompt: str = "") -> bytes: raise NotImplementedError("speech_to_speech non implémentée")
    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]: raise NotImplementedError("process_manga_page non implémentée")
    def inpaint_text_bubbles(self, image_data: bytes, text_placements: List[Dict]) -> str: raise NotImplementedError("inpaint_text_bubbles non implémentée")
    def generate_image_description(self, image_data: bytes, prompt: str = "") -> str: raise NotImplementedError("generate_image_description non implémentée")
    def get_diagnostics(self, prompt: str, completion: str) -> Dict[str, Any]: raise NotImplementedError("get_diagnostics non implémentée")
    def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]: raise NotImplementedError("calculate_uncertainty non implémentée")
    def estimate_depth(self, image_data: bytes) -> bytes: raise NotImplementedError("estimate_depth non implémentée")
    def generate_3d_scene(self, image_data: bytes, depth_map: bytes) -> Dict[str, Any]: raise NotImplementedError("generate_3d_scene non implémentée")
    
    def visual_rerank(self, query: str, image_urls: List[str], system_prompt: str = "") -> List[Dict[str, Any]]:
        raise NotImplementedError("visual_rerank non implémentée")
        
    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        raise NotImplementedError("moderate_content not implemented for BrainAPIAdapter")
        
    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]:
        raise NotImplementedError("get_multimodal_late_interaction non implémentée")

    def health_check(self) -> dict:
        if not self.brain_api_url: return {"status": "offline", "reason": "No URL"}
        try:
            res = requests.get(f"{self.brain_api_url}/health", timeout=5)
            if res.status_code == 200: return {"status": "online", "engine": "Brain-API"}
        except Exception as e:
            logger.error(f"BrainAPI Health check failed: {e}")
        return {"status": "offline", "engine": "Brain-API"}
