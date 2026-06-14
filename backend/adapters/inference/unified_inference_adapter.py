import os
import httpx
import json
import re
import time
import logging
import base64
import functools
from typing import Optional, List, Dict, Any
from core.ports.inference_port import InferencePort, InferenceNotImplementedError
from core.utils.security import is_safe_url, safe_http_request
from core.domain.exceptions import InferenceError
from core.domain.entities.ai_schemas import InferenceResponse, InferenceMetadata, TokenLogProb

# Focused Mixin imports
from adapters.inference.clip_vision import ClipVisionMixin
from adapters.inference.depth_estimation import DepthEstimationMixin
from adapters.inference.manga_ocr import MangaOcrMixin
from adapters.inference.video_analysis import VideoAnalysisMixin
from adapters.inference.audio_mixin import AudioMixin
from adapters.inference.image_gen_mixin import ImageGenMixin
from adapters.inference.vlm_mixin import VlmMixin
from adapters.inference.rerank_mixin import RerankMixin

logger = logging.getLogger("animetix." + __name__)

class UnifiedInferenceAdapter(
    ClipVisionMixin,
    DepthEstimationMixin,
    MangaOcrMixin,
    VideoAnalysisMixin,
    AudioMixin,
    ImageGenMixin,
    VlmMixin,
    RerankMixin,
    InferencePort
):
    """
    Unified Inference Adapter supporting local Ollama and OpenAI-compatible endpoints.
    Composes specialized mixins for vision, audio, and image generation as local fallbacks.
    """
    def __init__(
        self,
        api_base: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 90,
        usage_port: Optional[Any] = None
    ):
        super().__init__(usage_port=usage_port)
        # Default to local Ollama OpenAI-compatible endpoint
        self.api_base = api_base or os.getenv("LLM_API_BASE") or "http://localhost:11434/v1"
        self.model_name = model_name or os.getenv("LLM_MODEL_NAME") or "qwen3.5"
        self.api_key = api_key or os.getenv("LLM_API_KEY") or "ollama"
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Cache for diagnostics & advanced uncertainty
        self._last_completion = None
        self._last_logprobs = None

        if not is_safe_url(self.api_base, allow_internal=True):
            logger.warning(f"UnifiedInferenceAdapter: API base URL might be unsafe: {self.api_base}")

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
            # Utilisation de safe_http_request avec allow_internal=True car api_base est configuré
            res = safe_http_request("POST", url, json=payload, headers=self._get_headers(), timeout=self.timeout, allow_internal=True)
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
            res = safe_http_request("POST", direct_url, json=direct_payload, timeout=self.timeout, allow_internal=True)
            if res.status_code == 200:
                return res.json().get("embedding", [])
            
            res.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to generate text embedding via UnifiedInferenceAdapter: {e}")
            raise InferenceError(f"Embedding generation failed: {e}")
        return []

    def generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs
    ) -> InferenceResponse:
        json_mode = kwargs.get("json_mode", False)
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2 if json_mode else 0.7
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        if thinking_mode or thinking_budget > 0:
            payload["extra_body"] = {
                "thinking_budget": thinking_budget,
                "thinking_mode": thinking_mode
            }

        if include_logprobs:
            payload["logprobs"] = True
            payload["top_logprobs"] = 5

        last_error = None
        for attempt in range(self.max_retries):
            try:
                url = f"{self.api_base}/chat/completions"
                res = safe_http_request("POST", url, json=payload, headers=self._get_headers(), timeout=self.timeout, allow_internal=True)

                if res.status_code == 400 and "extra_body" in payload:
                    logger.warning("Target LLM server rejected thinking parameters, retrying without them.")
                    del payload["extra_body"]
                    res = safe_http_request("POST", url, json=payload, headers=self._get_headers(), timeout=self.timeout, allow_internal=True)
                
                if res.status_code == 400 and json_mode:
                    logger.warning("Target LLM server rejected JSON mode, retrying with raw text.")
                    del payload["response_format"]
                    res = safe_http_request("POST", url, json=payload, headers=self._get_headers(), timeout=self.timeout, allow_internal=True)

                res.raise_for_status()
                data = res.json()

                usage = data.get("usage", {})
                self._log_usage(
                    engine=f"unified:{self.model_name}",
                    input_tokens=usage.get("prompt_tokens", 0),
                    output_tokens=usage.get("completion_tokens", 0)
                )

                if isinstance(data, dict) and "choices" in data:
                    choice = data["choices"][0]
                    raw_content = choice["message"]["content"]
                    
                    # Extraction des logprobs si présentes
                    parsed_logprobs = None
                    if "logprobs" in choice and choice["logprobs"] and "content" in choice["logprobs"]:
                        parsed_logprobs = []
                        for lp in choice["logprobs"]["content"]:
                            top_lp = None
                            if "top_logprobs" in lp and lp["top_logprobs"]:
                                # Conversion vers List[Dict[str, float]] attendue par le schéma
                                top_lp = [{item["token"]: item["logprob"]} for item in lp["top_logprobs"]]
                            
                            parsed_logprobs.append(TokenLogProb(
                                token=lp["token"],
                                logprob=lp["logprob"],
                                top_logprobs=top_lp
                            ))
                else:
                    raw_content = str(data)
                    parsed_logprobs = None

                if "---" in raw_content:
                    raw_content = raw_content.split("---")[0].strip()

                self._last_completion = raw_content
                self._last_logprobs = parsed_logprobs

                return InferenceResponse(
                    text=raw_content,
                    metadata=InferenceMetadata(
                        logprobs=parsed_logprobs,
                        usage=usage
                    )
                )
            except httpx.RequestError as e:
                last_error = e
                logger.error(f"Inference attempt {attempt+1}/{self.max_retries} failed: {e}")
                time.sleep(1)
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error in UnifiedInferenceAdapter: {e}")
                break

        raise InferenceError(f"Le service d'inférence ({self.model_name}) est indisponible. Dernier essai: {last_error}")

    def stream_generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs
    ):
        self._last_completion = ""
        self._last_logprobs = []
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

        if include_logprobs:
            payload["logprobs"] = True
            payload["top_logprobs"] = 5

        url = f"{self.api_base}/chat/completions"
        try:
            # Sécurité SSRF: On valide l'URL avant le stream
            if not is_safe_url(url, allow_internal=True):
                 raise ValueError(f"Unsafe stream URL: {url}")

            with httpx.Client(timeout=self.timeout, follow_redirects=False) as client:
                with client.stream("POST", url, json=payload, headers=self._get_headers()) as res:
                    if res.status_code == 400 and "extra_body" in payload:
                        logger.warning("Target LLM server rejected thinking parameters for streaming, retrying without.")
                        # Retrying in a stream is complex, here we just return the error for now or would need to restart the loop
                        pass

                    res.raise_for_status()
                    for line in res.iter_lines():
                        if line:
                            if line.startswith("data: "):
                                data_content = line[6:].strip()
                                if data_content == "[DONE]":
                                    break
                                try:
                                    chunk = json.loads(data_content)
                                    choice = chunk['choices'][0]
                                    delta = choice.get('delta', {})
                                    
                                    # Extraction des logprobs par token si présentes dans le chunk
                                    parsed_logprobs = None
                                    if "logprobs" in choice and choice["logprobs"] and "content" in choice["logprobs"]:
                                        parsed_logprobs = []
                                        for lp in choice["logprobs"]["content"]:
                                            top_lp = None
                                            if "top_logprobs" in lp and lp["top_logprobs"]:
                                                # Conversion vers List[Dict[str, float]] attendue par le schéma
                                                top_lp = [{item["token"]: item["logprob"]} for item in lp["top_logprobs"]]

                                            parsed_logprobs.append(TokenLogProb(
                                                token=lp["token"],
                                                logprob=lp["logprob"],
                                                top_logprobs=top_lp
                                            ))

                                    if 'content' in delta:
                                        self._last_completion += delta['content']
                                        if parsed_logprobs:
                                            self._last_logprobs.extend(parsed_logprobs)
                                        yield InferenceResponse(
                                            text=delta['content'],
                                            metadata=InferenceMetadata(
                                                logprobs=parsed_logprobs,
                                                usage=chunk.get("usage")
                                            )
                                        )
                                except Exception as e:
                                    logger.warning(f"Error parsing stream chunk: {e}")
                                    continue
        except Exception as e:
            logger.error(f"Unified Stream Error: {e}")
            raise InferenceError(f"Streaming failed: {e}")

    def health_check(self) -> dict:
        try:
            res = safe_http_request("GET", f"{self.api_base.replace('/v1', '')}/api/tags", timeout=5, allow_internal=True)
            if res.status_code == 200:
                return {"status": "online", "engine": "Ollama/Unified", "models": res.json().get("models", [])}
        except Exception as e:
            logger.debug(f"Ollama health check failed: {e}")

        try:
            res = safe_http_request("GET", f"{self.api_base}/models", headers=self._get_headers(), timeout=5, allow_internal=True)
            if res.status_code == 200:
                return {"status": "online", "engine": "OpenAI-Compatible/Unified"}
        except Exception as e:
            logger.debug(f"OpenAI-Compatible health check failed: {e}")

        return {"status": "offline", "engine": "Unified"}

    def generate_sprite(self, prompt: str, style: str = "") -> str:
        """Génère un sprite de personnage (généralement sur fond transparent ou blanc)."""
        # Leveraging the existing generate_image from ImageGenMixin
        # Adding specific modifiers for sprite generation
        modified_prompt = (
            f"{prompt}, full body, character sheet, "
            f"transparent background, no shadows, clean lines, "
            f"digital art, high resolution, {style}"
        )
        return self.generate_image(modified_prompt, style)
