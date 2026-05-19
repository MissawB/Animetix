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

    def calculate_visual_similarity(self, query: str, item_id: str, media_type: str) -> float:
        logger.warning(f"calculate_visual_similarity not implemented for VllmAdapter")
        return 0.0

    def get_image_embedding(self, image_data: bytes, model_id: Optional[str] = None) -> List[float]:
        logger.warning(f"get_image_embedding not implemented for VllmAdapter")
        return []

    def classify_image(self, image_data: bytes, candidate_labels: List[str], model_id: Optional[str] = None) -> Dict[str, float]:
        """
        Classifie une image en utilisant le VLM.
        """
        try:
            import base64
            import json
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            prompt = f"Classify this image among these labels and return a JSON object with labels as keys and confidence scores as values: {', '.join(candidate_labels)}"
            
            res = requests.post(f"{self.api_base}/chat/completions", json={
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]}
                ],
                "response_format": {"type": "json_object"}
            }, timeout=30)
            res.raise_for_status()
            return json.loads(res.json()['choices'][0]['message']['content'])
        except Exception as e:
            logger.error(f"VLM Image Classification error: {e}")
            return {}
    def detect_objects(self, image_data: bytes, candidate_queries: List[str], model_id: Optional[str] = None) -> List[Dict]:
        """
        Détecte des objets en demandant au VLM de retourner des coordonnées.
        Note: Dépend de la capacité du modèle chargé (ex: Qwen-VL, Llava).
        """
        try:
            import base64
            import json
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            prompt = f"Detect these objects in the image and return a JSON list of objects with 'label', 'score', and 'box' [ymin, xmin, ymax, xmax]: {', '.join(candidate_queries)}"
            
            res = requests.post(f"{self.api_base}/chat/completions", json={
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]}
                ],
                "response_format": {"type": "json_object"}
            }, timeout=30)
            res.raise_for_status()
            data = res.json()['choices'][0]['message']['content']
            
            # Extraction JSON robuste
            try:
                detected = json.loads(data)
                return detected.get("objects", [])
            except:
                return []
        except Exception as e:
            logger.error(f"VLM Object Detection error: {e}")
            return []

    def get_video_temporal_embeddings(self, video_data: bytes) -> List[Dict[str, Any]]:
        logger.warning(f"get_video_temporal_embeddings not implemented for VllmAdapter")
        return []

    def localize_video_actions(self, video_data: bytes, action_queries: List[str]) -> List[Dict[str, Any]]:
        logger.warning(f"localize_video_actions not implemented for VllmAdapter")
        return []

    def transform_image_to_anime(self, image_data: bytes, studio_style: str, prompt: str = "") -> str:
        logger.warning(f"transform_image_to_anime not implemented for VllmAdapter")
        return ""

    def transform_video_to_anime(self, video_data: bytes, studio_style: str, prompt: str = "") -> str:
        logger.warning(f"transform_video_to_anime not implemented for VllmAdapter")
        return ""

    def generate_soundscape(self, video_metadata: Dict[str, Any], prompt: Optional[str] = None) -> str:
        logger.warning(f"generate_soundscape not implemented for VllmAdapter")
        return ""

    def clone_voice(self, text: str, reference_audio: bytes, language: str = "fr") -> bytes:
        logger.warning(f"clone_voice not implemented for VllmAdapter")
        return b""

    def speech_to_speech(self, audio_input: bytes, system_prompt: str = "") -> bytes:
        logger.warning(f"speech_to_speech not implemented for VllmAdapter")
        return b""

    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]:
        logger.warning(f"process_manga_page not implemented for VllmAdapter")
        return {}

    def translate_manga_page(self, image_data: bytes, target_lang: str = "Français") -> Dict[str, Any]:
        logger.warning(f"translate_manga_page not implemented for VllmAdapter")
        return {}

    def inpaint_text_bubbles(self, image_data: bytes, text_placements: List[Dict]) -> str:
        logger.warning(f"inpaint_text_bubbles not implemented for VllmAdapter")
        return ""

    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        logger.warning(f"moderate_content not implemented for VllmAdapter")
        return {}

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
    
    def visual_rerank(self, query: str, image_urls: List[str], system_prompt: str = "Tu es un expert en analyse visuelle d'anime.") -> List[Dict[str, Any]]:
        """Utilise le VLM pour classer une liste d'images par pertinence visuelle."""
        if not image_urls:
            return []

        # Construction du prompt. Si le query semble déjà être un prompt complexe (contient 'MISSION'), on l'utilise tel quel.
        if "MISSION" in query:
            prompt = query
        else:
            prompt = f"Analyse ces {len(image_urls)} images (indexées de 0 à {len(image_urls)-1}) et classe-les selon leur pertinence par rapport à la requête : '{query}'.\n" \
                     "Réponds uniquement sous forme de JSON avec la structure suivante : {\"scores\": [{\"index\": 0, \"score\": 0.95}, ...]}"

        content = [{"type": "text", "text": prompt}]
        for url in image_urls:
            content.append({"type": "image_url", "image_url": {"url": url}})

        try:
            import json
            import re
            res = requests.post(f"{self.api_base}/chat/completions", json={
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                "response_format": {"type": "json_object"}
            }, timeout=60)
            res.raise_for_status()
            raw_content = res.json()['choices'][0]['message']['content']
            
            # Extraction JSON robuste
            json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(raw_content)

            results = data.get("scores") or data.get("results") or []
            
            # Harmonisation : s'assurer qu'on a 'index' et 'score'
            # Si le modèle a retourné 'url', on tente de mapper vers l'index
            final_results = []
            for i, item in enumerate(results):
                idx = item.get("index")
                if idx is None and "url" in item:
                    # Fallback si le modèle a renvoyé l'URL au lieu de l'index
                    try:
                        idx = image_urls.index(item["url"])
                    except ValueError:
                        idx = i
                
                if idx is not None:
                    final_results.append({
                        "index": int(idx),
                        "score": float(item.get("score", 0.0))
                    })
            
            if not final_results:
                logger.warning("vLLM rerank returned no valid results. Using fallback.")
                return [{"index": i, "score": 1.0 / len(image_urls)} for i in range(len(image_urls))]
                
            return final_results
        except Exception as e:
            logger.error(f"vLLM visual rerank error: {e}")
            return [{"index": i, "score": 0.0} for i in range(len(image_urls))]

    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]:
        return []

    
    def generate_image(self, prompt: str, style: str = "") -> str:
        logger.warning(f"generate_image not implemented for VllmAdapter")
        return ""

    def health_check(self) -> dict:
        try:
            res = requests.get(f"{self.api_base}/models", timeout=5)
            if res.status_code == 200: return {"status": "online", "engine": "vLLM", "model": self.model_name}
        except Exception as e:
            logger.error(f"vLLM health check failed: {e}")
        return {"status": "offline", "engine": "vLLM"}
