import requests
import logging
from typing import Optional, List, Dict, Any
from core.ports.inference_port import InferencePort

logger = logging.getLogger("animetix.inference")

class VllmAdapter(InferencePort):
    def __init__(self, api_base: str = "http://localhost:8000/v1", model_name: str = "meta-llama/Llama-3-8B-Instruct"):
        self.api_base = api_base
        self.model_name = model_name

    def generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False) -> str:
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        
        # vLLM handles extra parameters in 'extra_body' or sometimes directly.
        # We try to pass them directly if requested, but we'll retry if the server complains.
        if thinking_mode or thinking_budget > 0:
            payload["extra_body"] = {
                "thinking_budget": thinking_budget,
                "thinking_mode": thinking_mode
            }

        try:
            res = requests.post(f"{self.api_base}/chat/completions", json=payload, timeout=30)
            
            # If 400 Bad Request, it might be due to unsupported extra parameters
            if res.status_code == 400 and "extra_body" in payload:
                logger.warning("vLLM server rejected extra_body (thinking parameters). Retrying without them.")
                del payload["extra_body"]
                res = requests.post(f"{self.api_base}/chat/completions", json=payload, timeout=30)
                
            res.raise_for_status()
            return res.json()['choices'][0]['message']['content']
        except requests.exceptions.ConnectionError:
            logger.error(f"vLLM server at {self.api_base} is unreachable.")
        except Exception as e:
            logger.error(f"vLLM Adapter error: {e}")
        return "Erreur: vLLM indisponible."

    def stream_generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False):
        # Implementation of streaming with fallback for robustness
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": True
        }
        if thinking_mode or thinking_budget > 0:
            payload["extra_body"] = {"thinking_budget": thinking_budget, "thinking_mode": thinking_mode}

        try:
            res = requests.post(f"{self.api_base}/chat/completions", json=payload, stream=True, timeout=30)
            if res.status_code == 400 and "extra_body" in payload:
                del payload["extra_body"]
                res = requests.post(f"{self.api_base}/chat/completions", json=payload, stream=True, timeout=30)
            
            res.raise_for_status()
            for line in res.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        data_content = line_str[6:]
                        if data_content == "[DONE]": break
                        import json
                        chunk = json.loads(data_content)
                        delta = chunk['choices'][0].get('delta', {})
                        if 'content' in delta: yield delta['content']
        except Exception as e:
            logger.error(f"vLLM Stream Error: {e}")
            yield self.generate(prompt, system_prompt, thinking_budget, thinking_mode)

    def calculate_visual_similarity(self, query: str, item_id: str, media_type: str) -> float: raise NotImplementedError()
    def get_image_embedding(self, image_data: bytes, model_id: Optional[str] = None) -> List[float]: raise NotImplementedError()
    def classify_image(self, image_data: bytes, candidate_labels: List[str], model_id: Optional[str] = None) -> Dict[str, float]: raise NotImplementedError()
    def detect_objects(self, image_data: bytes, candidate_queries: List[str], model_id: Optional[str] = None) -> List[Dict]: raise NotImplementedError()
    def get_video_temporal_embeddings(self, video_data: bytes) -> List[Dict[str, Any]]: raise NotImplementedError()
    def localize_video_actions(self, video_data: bytes, action_queries: List[str]) -> List[Dict[str, Any]]: raise NotImplementedError()
    def transform_image_to_anime(self, image_data: bytes, studio_style: str, prompt: str = "") -> str: raise NotImplementedError()
    def transform_video_to_anime(self, video_data: bytes, studio_style: str, prompt: str = "") -> str: raise NotImplementedError()
    def generate_soundscape(self, video_metadata: Dict[str, Any], prompt: Optional[str] = None) -> str: raise NotImplementedError()
    def clone_voice(self, text: str, reference_audio: bytes, language: str = "fr") -> bytes: raise NotImplementedError()
    def speech_to_speech(self, audio_input: bytes, system_prompt: str = "") -> bytes: raise NotImplementedError()
    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]: raise NotImplementedError()
    def inpaint_text_bubbles(self, image_data: bytes, text_placements: List[Dict]) -> str: raise NotImplementedError()
    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]: raise NotImplementedError()
    def generate_image_description(self, image_data: bytes, prompt: str = "Décris cette image d'anime de manière très détaillée.") -> str:
        """Utilise le VLM pour décrire une image."""
        try:
            import base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            # Envoi via l'API vLLM (multimodal support)
            res = requests.post(f"{self.api_base}/chat/completions", json={
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
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
