import os
import httpx
import time
import logging
from typing import Optional, List, Dict, Any
from core.ports.inference_port import InferencePort
from core.ports.usage_port import UsagePort
from core.utils.security import is_safe_url, validate_service_url, safe_http_request
from core.domain.entities.ai_schemas import InferenceResponse, InferenceMetadata, TokenLogProb

logger = logging.getLogger("animetix.inference")

class BrainAPIAdapter(InferencePort):
    def __init__(self, brain_api_url: str, brain_api_key: str, max_retries: int = 3, usage_port: Optional[UsagePort] = None):
        super().__init__(usage_port=usage_port)
        
        # Validation de l'URL du service (Protection contre injection de config)
        # On accepte soit un hostname local (docker/k8s), soit une URL sûre.
        self.brain_api_url = brain_api_url
        self.max_retries = max_retries
        self.brain_api_key = brain_api_key
        
        # Cache for diagnostics & advanced uncertainty
        self._last_completion = None
        self._last_logprobs = None
        
        if self.brain_api_url and not (
            self.brain_api_url.startswith("http://brain") or 
            self.brain_api_url.startswith("http://localhost") or
            is_safe_url(self.brain_api_url, allow_internal=True)
        ):
            logger.warning(f"Potentially unsafe BRAIN_API_URL configured: {self.brain_api_url}")

    def _get_headers(self) -> Dict[str, str]:
        return {"X-API-Key": self.brain_api_key}

    def generate(
        self, 
        prompt: str, 
        system_prompt: str = "", 
        thinking_budget: int = 0, 
        thinking_mode: bool = False,
        include_logprobs: bool = False
    ) -> InferenceResponse:
        if not self.brain_api_url: 
            return InferenceResponse(text="Erreur: BRAIN_API_URL non configurée.")
            
        for attempt in range(self.max_retries):
            try:
                # Utilisation de safe_http_request pour valider les redirections (en autorisant l'interne)
                res = safe_http_request("POST", f"{self.brain_api_url}/generate", json={
                    "prompt": prompt, 
                    "system_prompt": system_prompt,
                    "thinking_budget": thinking_budget,
                    "thinking_mode": thinking_mode,
                    "include_logprobs": include_logprobs
                }, headers=self._get_headers(), timeout=30, allow_internal=True)
                res.raise_for_status()
                data = res.json()
                text = data.get("text", "")
                
                # Log usage
                usage = data.get("usage", {})
                self._log_usage(
                    engine="brain:generate",
                    input_tokens=usage.get("prompt_tokens", len(prompt) // 4),
                    output_tokens=usage.get("completion_tokens", len(text) // 4)
                )

                # Parse logprobs if present
                parsed_logprobs = None
                if include_logprobs and "logprobs" in data:
                    parsed_logprobs = []
                    for lp in data["logprobs"]:
                        parsed_logprobs.append(TokenLogProb(
                            token=lp.get("token", ""),
                            logprob=lp.get("logprob", 0.0),
                            top_logprobs=lp.get("top_logprobs")
                        ))
                
                self._last_completion = text
                self._last_logprobs = parsed_logprobs
                
                return InferenceResponse(
                    text=text,
                    metadata=InferenceMetadata(
                        logprobs=parsed_logprobs,
                        usage=usage,
                        thinking=data.get("thinking")
                    )
                )
            except httpx.RequestError as e:
                logger.error(f"BrainAPI Request failed (Attempt {attempt+1}/{self.max_retries}): {e}")
                time.sleep(1)
            except Exception as e:
                logger.error(f"Unexpected BrainAPI error: {e}")
                break
        return InferenceResponse(text="Erreur: Le cerveau distant ne répond pas.")

    def stream_generate(
        self, 
        prompt: str, 
        system_prompt: str = "", 
        thinking_budget: int = 0, 
        thinking_mode: bool = False,
        include_logprobs: bool = False
    ):
        # Implementation of streaming depends on brain_api capability
        # For now, fallback to yielding a single InferenceResponse from generate
        yield self.generate(
            prompt, 
            system_prompt, 
            thinking_budget, 
            thinking_mode, 
            include_logprobs=include_logprobs
        )

    def calculate_visual_similarity(self, query: str, item_id: str, media_type: str) -> float:
        if not self.brain_api_url: return 0.0
        try:
            res = safe_http_request("POST", f"{self.brain_api_url}/similarity/visual", json={"query": query, "item_id": item_id, "media_type": media_type}, headers=self._get_headers(), timeout=10, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:similarity:visual", units=1)
                return res.json().get("score", 0.0)
        except Exception as e:
            logger.error(f"BrainAPI Visual Similarity error: {e}")
        return 0.0

    def get_image_embedding(self, image_data: bytes, model_id: Optional[str] = None) -> List[float]:
        if not self.brain_api_url: return []
        try:
            import base64
            b64 = base64.b64encode(image_data).decode('utf-8')
            res = safe_http_request("POST", f"{self.brain_api_url}/vision/embedding", json={"image": b64, "model_id": model_id}, headers=self._get_headers(), timeout=10, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:vision:embedding", units=1)
                return res.json().get("embedding", [])
        except Exception as e:
            logger.error(f"BrainAPI Image Embedding error: {e}")
        return []

    def detect_objects(self, image_data: bytes, candidate_queries: List[str], model_id: Optional[str] = None) -> List[Dict]:
        if not self.brain_api_url: return []
        try:
            import base64
            b64 = base64.b64encode(image_data).decode('utf-8')
            res = safe_http_request("POST", f"{self.brain_api_url}/vision/detect", json={
                "image": b64, 
                "candidate_labels": candidate_queries,
                "model_id": model_id
            }, headers=self._get_headers(), timeout=20, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:vision:detect", units=1)
                return res.json().get("objects", [])
        except Exception as e:
            logger.error(f"BrainAPI Object Detection error: {e}")
        return []

    def generate_image_description(self, image_data: bytes, prompt: str = "") -> str:
        if not self.brain_api_url: return ""
        try:
            import base64
            b64 = base64.b64encode(image_data).decode('utf-8')
            res = safe_http_request("POST", f"{self.brain_api_url}/vision/describe", json={
                "image": b64, 
                "prompt": prompt
            }, headers=self._get_headers(), timeout=30, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:vision:describe", units=1)
                return res.json().get("description", "")
        except Exception as e:
            logger.error(f"BrainAPI Image Description error: {e}")
        return ""

    def estimate_depth(self, image_data: bytes) -> bytes:
        if not self.brain_api_url: return b""
        try:
            import base64
            b64 = base64.b64encode(image_data).decode('utf-8')
            res = safe_http_request("POST", f"{self.brain_api_url}/vision/depth", json={"image": b64}, headers=self._get_headers(), timeout=20, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:vision:depth", units=1)
                return base64.b64decode(res.json().get("depth_b64", ""))
        except Exception as e:
            logger.error(f"BrainAPI Depth Estimation error: {e}")
        return b""

    def visual_rerank(self, query: str, image_urls: List[str], system_prompt: str = "") -> List[Dict[str, Any]]:
        if not self.brain_api_url: return []
        
        # Sécurité SSRF: Filtrer les URLs d'images non-sûres
        safe_urls = [url for url in image_urls if is_safe_url(url)]
        if not safe_urls:
             logger.warning("No safe URLs provided for visual rerank.")
             return []

        try:
            res = safe_http_request("POST", f"{self.brain_api_url}/vision/rerank", json={
                "query": query, 
                "image_urls": safe_urls,
                "system_prompt": system_prompt
            }, headers=self._get_headers(), timeout=30, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:vision:rerank", units=1)
                return res.json().get("reranked_items", [])
        except Exception as e:
            logger.error(f"BrainAPI Visual Rerank error: {e}")
        return []

    def classify_image(self, image_data: bytes, candidate_labels: List[str], model_id: Optional[str] = None) -> Dict[str, float]:
        if not self.brain_api_url: return {}
        try:
            import base64
            b64 = base64.b64encode(image_data).decode('utf-8')
            res = safe_http_request("POST", f"{self.brain_api_url}/vision/classify", json={
                "image": b64, 
                "candidate_labels": candidate_labels,
                "model_id": model_id
            }, headers=self._get_headers(), timeout=20, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:vision:classify", units=1)
                return res.json().get("labels", {})
        except Exception as e:
            logger.error(f"BrainAPI Image Classification error: {e}")
        return {}

    def get_video_temporal_embeddings(self, video_data: bytes) -> List[Dict[str, Any]]:
        if not self.brain_api_url: return []
        try:
            import base64
            b64 = base64.b64encode(video_data).decode('utf-8')
            res = safe_http_request("POST", f"{self.brain_api_url}/video/embeddings", json={"video": b64}, headers=self._get_headers(), timeout=60, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:video:embeddings", units=1)
                return res.json().get("embeddings", [])
        except Exception as e:
            logger.error(f"BrainAPI Video Temporal Embeddings error: {e}")
        return []

    def localize_video_actions(self, video_data: bytes, action_queries: List[str]) -> List[Dict[str, Any]]:
        if not self.brain_api_url: return []
        try:
            import base64
            b64 = base64.b64encode(video_data).decode('utf-8')
            res = safe_http_request("POST", f"{self.brain_api_url}/video/localize", json={
                "video": b64, 
                "queries": action_queries
            }, headers=self._get_headers(), timeout=60, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:video:localize", units=1)
                return res.json().get("actions", [])
        except Exception as e:
            logger.error(f"BrainAPI Video Action Localization error: {e}")
        return []
    def transform_image_to_anime(self, image_data: bytes, studio_style: str, prompt: str = "") -> str:
        if not self.brain_api_url: return ""
        try:
            import base64
            b64 = base64.b64encode(image_data).decode('utf-8')
            res = safe_http_request("POST", f"{self.brain_api_url}/vision/transform/anime", json={
                "image": b64, 
                "studio_style": studio_style,
                "prompt": prompt
            }, headers=self._get_headers(), timeout=45, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:vision:transform:anime", units=1)
                return res.json().get("image_url_or_b64", "")
        except Exception as e:
            logger.error(f"BrainAPI Image to Anime error: {e}")
        return ""

    def transform_video_to_anime(self, video_data: bytes, studio_style: str, prompt: str = "") -> str:
        if not self.brain_api_url: return ""
        try:
            import base64
            b64 = base64.b64encode(video_data).decode('utf-8')
            res = safe_http_request("POST", f"{self.brain_api_url}/video/transform/anime", json={
                "video": b64, 
                "studio_style": studio_style,
                "prompt": prompt
            }, headers=self._get_headers(), timeout=120, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:video:transform:anime", units=1)
                return res.json().get("video_url_or_b64", "")
        except Exception as e:
            logger.error(f"BrainAPI Video to Anime error: {e}")
        return ""

    def generate_soundscape(self, video_metadata: Dict[str, Any], prompt: Optional[str] = None) -> str:
        if not self.brain_api_url: return ""
        try:
            res = safe_http_request("POST", f"{self.brain_api_url}/audio/generate/soundscape", json={
                "video_metadata": video_metadata,
                "prompt": prompt
            }, headers=self._get_headers(), timeout=30, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:audio:soundscape", units=1)
                return res.json().get("audio_url_or_b64", "")
        except Exception as e:
            logger.error(f"BrainAPI Soundscape Generation error: {e}")
        return ""
    def clone_voice(self, text: str, reference_audio: bytes, language: str = "fr") -> bytes:
        if not self.brain_api_url: return b""
        try:
            import base64
            b64 = base64.b64encode(reference_audio).decode('utf-8')
            res = safe_http_request("POST", f"{self.brain_api_url}/audio/clone-voice", json={
                "text": text, 
                "reference_audio": b64,
                "language": language
            }, headers=self._get_headers(), timeout=30, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:audio:clone_voice", units=1)
                return base64.b64decode(res.json().get("audio_b64", ""))
        except Exception as e:
            logger.error(f"BrainAPI Voice Cloning error: {e}")
        return b""

    def speech_to_speech(self, audio_input: bytes, system_prompt: str = "") -> bytes:
        if not self.brain_api_url: return b""
        try:
            import base64
            b64 = base64.b64encode(audio_input).decode('utf-8')
            res = safe_http_request("POST", f"{self.brain_api_url}/audio/speech-to-speech", json={
                "audio": b64, 
                "system_prompt": system_prompt
            }, headers=self._get_headers(), timeout=30, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:audio:speech_to_speech", units=1)
                return base64.b64decode(res.json().get("audio_b64", ""))
        except Exception as e:
            logger.error(f"BrainAPI Speech-to-Speech error: {e}")
        return b""
    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]:
        if not self.brain_api_url: return {}
        try:
            import base64
            b64 = base64.b64encode(image_data).decode('utf-8')
            res = safe_http_request("POST", f"{self.brain_api_url}/vision/manga/process", json={"image": b64}, headers=self._get_headers(), timeout=30, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:vision:manga:process", units=1)
                return res.json()
        except Exception as e:
            logger.error(f"BrainAPI Manga Process error: {e}")
        return {}

    def translate_manga_page(self, image_data: bytes, target_lang: str = "Français") -> Dict[str, Any]:
        if not self.brain_api_url: return {}
        try:
            import base64
            b64 = base64.b64encode(image_data).decode('utf-8')
            res = safe_http_request("POST", f"{self.brain_api_url}/vision/manga/translate", json={"image": b64, "target_lang": target_lang}, headers=self._get_headers(), timeout=60, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:vision:manga:translate", units=1)
                return res.json()
        except Exception as e:
            logger.error(f"BrainAPI Manga Translate error: {e}")
        return {}
    def inpaint_text_bubbles(self, image_data: bytes, text_placements: List[Dict]) -> str:
        if not self.brain_api_url: return ""
        try:
            import base64
            b64 = base64.b64encode(image_data).decode('utf-8')
            res = safe_http_request("POST", f"{self.brain_api_url}/vision/manga/inpaint", json={
                "image": b64, 
                "text_placements": text_placements
            }, headers=self._get_headers(), timeout=30, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:vision:manga:inpaint", units=1)
                return res.json().get("image_url_or_b64", "")
        except Exception as e:
            logger.error(f"BrainAPI Manga Inpaint error: {e}")
        return ""
    def get_diagnostics(self, prompt: str, completion: str) -> Dict[str, Any]:
        if not self.brain_api_url: return {}
        try:
            res = safe_http_request("POST", f"{self.brain_api_url}/diagnostics", json={
                "prompt": prompt, 
                "completion": completion
            }, headers=self._get_headers(), timeout=10, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:diagnostics", units=1)
                return res.json().get("diagnostics", {})
        except Exception as e:
            logger.error(f"BrainAPI Diagnostics error: {e}")
        return {}

    def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]:
        try:
            if getattr(self, "_last_completion", None) == completion and getattr(self, "_last_logprobs", None):
                logprobs = [lp.logprob for lp in self._last_logprobs if lp.logprob is not None]
                if logprobs:
                    import numpy as np
                    avg_entropy = -sum(logprobs) / len(logprobs)
                    confidence = max(0.0, min(1.0, 1.0 - (avg_entropy / 10.8)))
                    perplexity = float(np.exp(avg_entropy))
                    logger.info("📊 BrainAPIAdapter: Using real logprobs from cache.")
                    return {
                        "entropy": round(avg_entropy, 4),
                        "perplexity": round(perplexity, 4),
                        "confidence": round(confidence, 4)
                    }
        except Exception as e:
            logger.warning(f"Failed to calculate uncertainty from cache: {e}")

        if not self.brain_api_url: return {}
        try:
            res = safe_http_request("POST", f"{self.brain_api_url}/uncertainty", json={
                "prompt": prompt, 
                "completion": completion
            }, headers=self._get_headers(), timeout=10, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:uncertainty", units=1)
                return res.json().get("uncertainty_metrics", {})
        except Exception as e:
            logger.error(f"BrainAPI Uncertainty calculation error: {e}")
        return {}
    def generate_3d_scene(self, image_data: bytes, depth_map: bytes) -> Dict[str, Any]:
        if not self.brain_api_url: return {}
        try:
            import base64
            img_b64 = base64.b64encode(image_data).decode('utf-8')
            depth_b64 = base64.b64encode(depth_map).decode('utf-8')
            res = safe_http_request("POST", f"{self.brain_api_url}/vision/generate-3d", json={
                "image": img_b64, 
                "depth_map": depth_b64
            }, headers=self._get_headers(), timeout=60, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:vision:generate_3d", units=1)
                return res.json().get("scene_data", {})
        except Exception as e:
            logger.error(f"BrainAPI 3D Scene Generation error: {e}")
        return {}
        
    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        if not self.brain_api_url: return {}
        try:
            res = safe_http_request("POST", f"{self.brain_api_url}/moderate", json={
                "text": text, 
                "categories": categories
            }, headers=self._get_headers(), timeout=10, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:moderate", units=1)
                return res.json().get("moderation", {})
        except Exception as e:
            logger.error(f"BrainAPI Moderation error: {e}")
        return {}
        
    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]:
        if not self.brain_api_url: return []
        try:
            import base64
            b64 = base64.b64encode(image_data).decode('utf-8')
            res = safe_http_request("POST", f"{self.brain_api_url}/vision/late-interaction", json={"image": b64}, headers=self._get_headers(), timeout=20, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:vision:late_interaction", units=1)
                return res.json().get("embeddings", [])
        except Exception as e:
            logger.error(f"BrainAPI Multimodal Late Interaction error: {e}")
        return []

    
    def generate_image(self, prompt: str, style: str = "") -> str:
        if not self.brain_api_url: return ""
        try:
            res = safe_http_request("POST", f"{self.brain_api_url}/vision/generate", json={
                "prompt": prompt, 
                "style": style
            }, headers=self._get_headers(), timeout=45, allow_internal=True)
            if res.status_code == 200:
                self._log_usage(engine="brain:vision:generate_image", units=1)
                return res.json().get("image_url_or_b64", "")
        except Exception as e:
            logger.error(f"BrainAPI Image Generation error: {e}")
        return ""

    def health_check(self) -> dict:
        if not self.brain_api_url: return {"status": "offline", "reason": "No URL"}
        try:
            res = safe_http_request("GET", f"{self.brain_api_url}/health", headers=self._get_headers(), timeout=5, allow_internal=True)
            if res.status_code == 200: return {"status": "online", "engine": "Brain-API"}
        except Exception as e:
            logger.error(f"BrainAPI Health check failed: {e}")
        return {"status": "offline", "engine": "Brain-API"}

    def generate_structured(self, prompt: str, response_model: type, system_prompt: str = "Tu es un expert en extraction de données structurées.", max_retries: int = 3) -> Any:
        """Génération structurée via le Cerveau distant (compatible OpenAI/Instructor)."""
        try:
            import instructor
            from openai import OpenAI
            
            # Note: On suppose que brain_api_url pointe vers la racine de l'API compatible OpenAI (ex: http://brain:5000/v1)
            # Si brain_api_url est juste l'URL de base sans /v1, il faudra peut-être l'ajouter.
            base_url = self.brain_api_url
            if not base_url.endswith("/v1") and "/generate" not in base_url:
                # Heuristique si besoin, mais on reste sur brain_api_url pour l'instant
                pass

            client = instructor.from_openai(
                OpenAI(base_url=base_url, api_key="not-needed"),
                mode=instructor.Mode.JSON
            )
            
            # Log heuristic usage
            self._log_usage(
                engine="brain:generate:structured",
                input_tokens=len(prompt) // 4,
                output_tokens=256
            )

            return client.chat.completions.create(
                model="brain-default", # Nom du modèle par défaut pour le cerveau
                response_model=response_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_retries=max_retries
            )
        except Exception as e:
            logger.error(f"BrainAPI Structured Generation failed: {e}")
            raise

