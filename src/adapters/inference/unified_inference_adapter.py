import os
import requests
import json
import time
import logging
import base64
from typing import Optional, List, Dict, Any
from core.ports.inference_port import InferencePort

logger = logging.getLogger("animetix.inference.unified")

class UnifiedInferenceAdapter(InferencePort):
    """
    Unified Inference Adapter supporting local Ollama, vLLM, and OpenAI-compatible endpoints.
    Allows easy environment configuration.
    """
    def __init__(
        self,
        api_base: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 90
    ):
        # Default to local Ollama OpenAI-compatible endpoint
        self.api_base = api_base or os.getenv("LLM_API_BASE") or "http://localhost:11434/v1"
        self.model_name = model_name or os.getenv("LLM_MODEL_NAME") or "llama3"
        self.api_key = api_key or os.getenv("LLM_API_KEY") or "ollama"
        self.max_retries = max_retries
        self.timeout = timeout

        logger.info(f"Initialized UnifiedInferenceAdapter for {self.model_name} at {self.api_base}")

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def get_text_embedding(self, text: str) -> List[float]:
        """Génère un embedding vectoriel pour un texte donné."""
        try:
            url = f"{self.api_base}/embeddings"
            payload = {
                "model": self.model_name,
                "input": text
            }
            res = requests.post(url, json=payload, headers=self._get_headers(), timeout=self.timeout)
            if res.status_code == 200:
                data = res.json()
                if "data" in data and len(data["data"]) > 0:
                    return data["data"][0]["embedding"]
                elif "embedding" in data:
                    return data["embedding"]
            
            # Fallback to direct Ollama api
            direct_url = f"{self.api_base.replace('/v1', '')}/api/embeddings"
            direct_payload = {
                "model": self.model_name,
                "prompt": text
            }
            res = requests.post(direct_url, json=direct_payload, timeout=self.timeout)
            if res.status_code == 200:
                return res.json().get("embedding", [])
        except Exception as e:
            logger.error(f"Failed to generate text embedding via UnifiedInferenceAdapter: {e}")
        return []

    def generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        json_mode: bool = False
    ) -> str:
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2 if json_mode else 0.7
        }

        if json_mode:
            # Standard OpenAI/vLLM/Ollama way to request JSON
            payload["response_format"] = {"type": "json_object"}

        # Handle deep reasoning parameters if requested
        if thinking_mode or thinking_budget > 0:
            payload["extra_body"] = {
                "thinking_budget": thinking_budget,
                "thinking_mode": thinking_mode
            }

        last_error = None
        for attempt in range(self.max_retries):
            try:
                url = f"{self.api_base}/chat/completions"
                res = requests.post(url, json=payload, headers=self._get_headers(), timeout=self.timeout)

                # Retry without thinking params if bad request
                if res.status_code == 400 and "extra_body" in payload:
                    logger.warning("Target LLM server rejected thinking parameters, retrying without them.")
                    del payload["extra_body"]
                    res = requests.post(url, json=payload, headers=self._get_headers(), timeout=self.timeout)
                
                # Retry without json_mode if 400 (some old Ollama versions might not like response_format)
                if res.status_code == 400 and json_mode:
                    logger.warning("Target LLM server rejected JSON mode, retrying with raw text.")
                    del payload["response_format"]
                    res = requests.post(url, json=payload, headers=self._get_headers(), timeout=self.timeout)

                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"]
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.error(f"Inference attempt {attempt+1}/{self.max_retries} failed: {e}")
                time.sleep(1)
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error in UnifiedInferenceAdapter: {e}")
                break

        return f"Erreur: Le service d'inférence ({self.model_name}) est indisponible. Erreur: {last_error}"

    def generate_structured(self, prompt: str, response_model: Any, system_prompt: str = "", max_retries: int = 3) -> Any:
        """
        Implementation of structured generation for UnifiedInferenceAdapter.
        Uses JSON mode and manual Pydantic validation.
        """
        try:
            # We use the existing generate with json_mode=True
            raw_json = self.generate(prompt, system_prompt=system_prompt, json_mode=True)
            
            # Robust extraction in case the model added markdown blocks despite JSON mode
            import json
            import re
            
            clean_json = raw_json.strip()
            if "```" in clean_json:
                match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_json, re.DOTALL | re.IGNORECASE)
                if match:
                    clean_json = match.group(1)
                else:
                    # Try to find first { and last }
                    start = clean_json.find('{')
                    end = clean_json.rfind('}')
                    if start != -1 and end != -1:
                        clean_json = clean_json[start:end+1]

            data = json.loads(clean_json)
            return response_model.model_validate(data)
        except Exception as e:
            logger.error(f"Failed structured generation in UnifiedInferenceAdapter: {e}")
            raise


    def stream_generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False
    ):
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "stream": True
        }

        if thinking_mode or thinking_budget > 0:
            payload["extra_body"] = {
                "thinking_budget": thinking_budget,
                "thinking_mode": thinking_mode
            }

        url = f"{self.api_base}/chat/completions"
        try:
            res = requests.post(url, json=payload, headers=self._get_headers(), stream=True, timeout=self.timeout)

            # Retry without extra body
            if res.status_code == 400 and "extra_body" in payload:
                logger.warning("Target LLM server rejected thinking parameters for streaming, retrying without.")
                del payload["extra_body"]
                res = requests.post(url, json=payload, headers=self._get_headers(), stream=True, timeout=self.timeout)

            res.raise_for_status()
            for line in res.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        data_content = line_str[6:].strip()
                        if data_content == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_content)
                            delta = chunk['choices'][0].get('delta', {})
                            if 'content' in delta:
                                yield delta['content']
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f"Unified Stream Error: {e}")
            yield self.generate(prompt, system_prompt, thinking_budget, thinking_mode)

    # --- Fallbacks / Stubs for Other Abstract Methods of InferencePort ---

    def generate_image(self, prompt: str, style: str = "") -> str:
        logger.warning("generate_image is not natively supported by standard LLM inference. Returning empty URL.")
        return ""

    def calculate_visual_similarity(self, query: str, item_id: str, media_type: str) -> float:
        logger.warning("calculate_visual_similarity is stubbed on UnifiedInferenceAdapter.")
        return 0.5

    def get_image_embedding(self, image_data: bytes, model_id: Optional[str] = None) -> List[float]:
        logger.warning("get_image_embedding is stubbed on UnifiedInferenceAdapter.")
        return []

    def classify_image(self, image_data: bytes, candidate_labels: List[str], model_id: Optional[str] = None) -> Dict[str, float]:
        logger.warning("classify_image is stubbed on UnifiedInferenceAdapter.")
        return {label: 1.0 / len(candidate_labels) for label in candidate_labels}

    def detect_objects(self, image_data: bytes, candidate_queries: List[str], model_id: Optional[str] = None) -> List[Dict]:
        logger.warning("detect_objects is stubbed on UnifiedInferenceAdapter.")
        return []

    def get_video_temporal_embeddings(self, video_data: bytes) -> List[Dict[str, Any]]:
        logger.warning("get_video_temporal_embeddings is stubbed on UnifiedInferenceAdapter.")
        return []

    def localize_video_actions(self, video_data: bytes, action_queries: List[str]) -> List[Dict[str, Any]]:
        logger.warning("localize_video_actions is stubbed on UnifiedInferenceAdapter.")
        return []

    def transform_image_to_anime(self, image_data: bytes, studio_style: str, prompt: str = "") -> str:
        logger.warning("transform_image_to_anime is stubbed on UnifiedInferenceAdapter.")
        return ""

    def transform_video_to_anime(self, video_data: bytes, studio_style: str, prompt: str = "") -> str:
        logger.warning("transform_video_to_anime is stubbed on UnifiedInferenceAdapter.")
        return ""

    def generate_soundscape(self, video_metadata: Dict[str, Any], prompt: Optional[str] = None) -> str:
        logger.warning("generate_soundscape is stubbed on UnifiedInferenceAdapter.")
        return ""

    def clone_voice(self, text: str, reference_audio: bytes, language: str = "fr") -> bytes:
        logger.warning("clone_voice is stubbed on UnifiedInferenceAdapter.")
        return b""

    def speech_to_speech(self, audio_input: bytes, system_prompt: str = "") -> bytes:
        logger.warning("speech_to_speech is stubbed on UnifiedInferenceAdapter.")
        return b""

    def estimate_depth(self, image_data: bytes) -> bytes:
        logger.warning("estimate_depth is stubbed on UnifiedInferenceAdapter.")
        return b""

    def generate_3d_scene(self, image_data: bytes, depth_map: bytes) -> Dict[str, Any]:
        logger.warning("generate_3d_scene is stubbed on UnifiedInferenceAdapter.")
        return {}

    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]:
        logger.warning("process_manga_page is stubbed on UnifiedInferenceAdapter.")
        return {}

    def translate_manga_page(self, image_data: bytes, target_lang: str = "Français") -> Dict[str, Any]:
        logger.warning("translate_manga_page is stubbed on UnifiedInferenceAdapter.")
        return {}

    def inpaint_text_bubbles(self, image_data: bytes, text_placements: List[Dict]) -> str:
        logger.warning("inpaint_text_bubbles is stubbed on UnifiedInferenceAdapter.")
        return ""

    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        logger.warning("moderate_content is stubbed on UnifiedInferenceAdapter.")
        return {"flagged": False, "scores": {}}

    def generate_image_description(self, image_data: bytes, prompt: str = "Décris cette image d'anime de manière très détaillée.") -> str:
        """Utilise un VLM si le endpoint d'inférence supporte les requêtes multimodales."""
        try:
            base64_image = base64.b64encode(image_data).decode('utf-8')
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ]
                    }
                ]
            }
            res = requests.post(f"{self.api_base}/chat/completions", json=payload, headers=self._get_headers(), timeout=self.timeout)
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Unified multimodal description failed: {e}. Retrying as pure text generation.")
            return self.generate(prompt)

    def get_diagnostics(self, prompt: str, completion: str) -> Dict[str, Any]:
        logger.warning("get_diagnostics is stubbed on UnifiedInferenceAdapter.")
        return {}

    def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]:
        logger.warning("calculate_uncertainty is stubbed on UnifiedInferenceAdapter.")
        return {}

    def health_check(self) -> dict:
        try:
            # Simple ping to Ollama or target server
            res = requests.get(f"{self.api_base.replace('/v1', '')}/api/tags", timeout=5)
            if res.status_code == 200:
                return {"status": "online", "engine": "Ollama/Unified", "models": res.json().get("models", [])}
        except Exception:
            pass

        try:
            res = requests.get(f"{self.api_base}/models", headers=self._get_headers(), timeout=5)
            if res.status_code == 200:
                return {"status": "online", "engine": "OpenAI-Compatible/Unified"}
        except Exception:
            pass

        return {"status": "offline", "engine": "Unified"}

    def visual_rerank(
        self, 
        query: str, 
        image_urls: List[str], 
        system_prompt: str = "Tu es un expert en analyse visuelle d'anime."
    ) -> List[Dict[str, Any]]:
        logger.warning("visual_rerank is stubbed on UnifiedInferenceAdapter.")
        return [{"index": i, "image_url": url, "score": 1.0 / len(image_urls)} for i, url in enumerate(image_urls)]

    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]:
        logger.warning("get_multimodal_late_interaction is stubbed on UnifiedInferenceAdapter.")
        return []
