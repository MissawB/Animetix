import os
import httpx
import time
import logging
import base64
from typing import Optional, List, Dict, Any
from core.ports.inference_port import InferencePort, InferenceNotImplementedError
from core.ports.usage_port import UsagePort
from core.utils.security import safe_http_request
from core.domain.entities.ai_schemas import (
    InferenceResponse,
    InferenceMetadata,
    TokenLogProb,
)

logger = logging.getLogger("animetix.inference.brain")


class BrainAPIAdapter(InferencePort):
    """
    Client pour l'API centrale d'Animetix (Brain), orchestrant les modèles SOTA.
    """

    def __init__(
        self,
        api_url: str = None,
        api_key: str = None,
        usage_port: Optional[UsagePort] = None,
    ):
        super().__init__(usage_port=usage_port)
        self.api_url = api_url or os.getenv("BRAIN_API_URL")
        self.api_key = api_key or os.getenv("BRAIN_API_KEY")

    def _get_headers(self) -> Dict[str, str]:
        return {"X-API-Key": self.api_key} if self.api_key else {}

    def generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs,
    ) -> InferenceResponse:
        """Appelle l'API Brain pour générer du texte."""
        if not self.api_url:
            raise ValueError("Brain API URL not configured")

        payload = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "thinking_budget": thinking_budget,
            "thinking_mode": thinking_mode,
            "include_logprobs": include_logprobs,
            **kwargs,
        }

        try:
            response = safe_http_request(
                "POST",
                f"{self.api_url}/generate",
                json=payload,
                headers=self._get_headers(),
            )
            data = response.json()

            self._log_usage(
                engine="brain:api",
                input_tokens=data.get("usage", {}).get("prompt_tokens", 0),
                output_tokens=data.get("usage", {}).get("completion_tokens", 0),
                allocated_budget=thinking_budget,
            )

            logprobs = None
            if "logprobs" in data and data["logprobs"] is not None:
                logprobs = [
                    TokenLogProb(token=lp["token"], logprob=lp["logprob"])
                    for lp in data["logprobs"]
                ]

            metadata = InferenceMetadata(
                logprobs=logprobs,
                usage=data.get("usage"),
                thinking=data.get("thinking"),
            )
            return InferenceResponse(text=data["text"], metadata=metadata)
        except Exception as e:
            logger.error(f"BrainAPI Generation failed: {e}")
            raise

    def stream_generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs,
    ):
        """Appelle l'API Brain pour générer du texte en streaming."""
        if not self.api_url:
            raise ValueError("Brain API URL not configured")

        payload = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "thinking_budget": thinking_budget,
            "thinking_mode": thinking_mode,
            "include_logprobs": include_logprobs,
            **kwargs,
        }

        try:
            with (
                httpx.stream(
                    "POST",
                    f"{self.api_url}/stream_generate",  # Assuming a dedicated streaming endpoint
                    json=payload,
                    headers=self._get_headers(),
                    timeout=None,  # Streaming responses can take a long time  # nosec B113
                ) as response
            ):
                response.raise_for_status()
                for (
                    chunk
                ) in response.iter_text():  # Or iter_bytes() if chunks are not text
                    yield InferenceResponse(text=chunk)
        except httpx.HTTPStatusError as e:
            logger.error(f"BrainAPI Streaming Generation HTTP error: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"BrainAPI Streaming Generation network error: {e}")
            raise
        except Exception as e:
            logger.error(f"BrainAPI Streaming Generation failed: {e}")
            raise

    def get_text_embedding(self, text: str) -> List[float]:
        """Appelle l'API Brain pour générer un embedding."""
        try:
            response = safe_http_request(
                "POST",
                f"{self.api_url}/v1/embeddings",  # Note: Verify if it's /v1/embeddings or just /embeddings
                json={"text": text},
                headers=self._get_headers(),
            )
            data = response.json()
            self._log_usage(engine="brain:embeddings", units=1)
            return data["embedding"]
        except Exception as e:
            logger.error(f"BrainAPI Embedding failed: {e}")
            raise

    def generate_image(self, prompt: str, style: str = "") -> str:
        try:
            response = safe_http_request(
                "POST",
                f"{self.api_url}/vision/generate",
                json={"prompt": prompt, "style": style},
                headers=self._get_headers(),
            )
            return response.json()["image_url_or_b64"]
        except Exception as e:
            logger.error(f"BrainAPI Image Generation failed: {e}")
            raise

    def generate_sprite(self, prompt: str, style: str = "") -> str:
        """Génère un sprite de personnage via Brain API."""
        sprite_prompt = (
            f"character sprite, full body standing, anime style, {prompt}, "
            f"centered, isolated on pure white background, masterpiece, high quality, "
            f"game asset, concept art"
        )
        try:
            return self.generate_image(sprite_prompt, style)
        except Exception as e:
            logger.error(f"BrainAPI Sprite Generation failed: {e}")
            raise InferenceNotImplementedError(
                f"BrainAPI Sprite Generation failed: {e}"
            )

    def get_image_embedding(
        self, image_data: bytes, model_id: Optional[str] = None
    ) -> List[float]:
        if not self.api_url:
            return []
        try:
            img_b64 = base64.b64encode(image_data).decode("utf-8")
            response = safe_http_request(
                "POST",
                f"{self.api_url}/vision/embedding",
                json={"image": img_b64, "model_id": model_id},
                headers=self._get_headers(),
            )
            return response.json()["embedding"]
        except Exception as e:
            logger.error(f"BrainAPI Image Embedding failed: {e}")
            raise

    def classify_image(
        self,
        image_data: bytes,
        candidate_labels: List[str],
        model_id: Optional[str] = None,
    ) -> Dict[str, float]:
        try:
            img_b64 = base64.b64encode(image_data).decode("utf-8")
            response = safe_http_request(
                "POST",
                f"{self.api_url}/vision/classify",
                json={
                    "image": img_b64,
                    "candidate_labels": candidate_labels,
                    "model_id": model_id,
                },
                headers=self._get_headers(),
            )
            return response.json()["labels"]
        except Exception as e:
            logger.error(f"BrainAPI Image Classify failed: {e}")
            raise

    def detect_objects(
        self,
        image_data: bytes,
        candidate_queries: List[str],
        model_id: Optional[str] = None,
    ) -> List[Dict]:
        try:
            img_b64 = base64.b64encode(image_data).decode("utf-8")
            response = safe_http_request(
                "POST",
                f"{self.api_url}/vision/detect",
                json={
                    "image": img_b64,
                    "candidate_labels": candidate_queries,
                    "model_id": model_id,
                },
                headers=self._get_headers(),
            )
            return response.json()["objects"]
        except Exception as e:
            logger.error(f"BrainAPI Object Detection failed: {e}")
            raise

    def get_video_temporal_embeddings(self, video_data: bytes) -> List[Dict[str, Any]]:
        try:
            vid_b64 = base64.b64encode(video_data).decode("utf-8")
            response = safe_http_request(
                "POST",
                f"{self.api_url}/video/embeddings",
                json={"video": vid_b64},
                headers=self._get_headers(),
            )
            return response.json()["embeddings"]
        except Exception as e:
            logger.error(f"BrainAPI Video Embeddings failed: {e}")
            raise

    def localize_video_actions(
        self, video_data: bytes, action_queries: List[str]
    ) -> List[Dict[str, Any]]:
        try:
            vid_b64 = base64.b64encode(video_data).decode("utf-8")
            response = safe_http_request(
                "POST",
                f"{self.api_url}/video/localize",
                json={"video": vid_b64, "queries": action_queries},
                headers=self._get_headers(),
            )
            return response.json()["actions"]
        except Exception as e:
            logger.error(f"BrainAPI Video Localization failed: {e}")
            raise

    def transform_image_to_anime(
        self, image_data: bytes, studio_style: str, prompt: str = ""
    ) -> str:
        try:
            img_b64 = base64.b64encode(image_data).decode("utf-8")
            response = safe_http_request(
                "POST",
                f"{self.api_url}/vision/transform/anime",
                json={"image": img_b64, "studio_style": studio_style, "prompt": prompt},
                headers=self._get_headers(),
            )
            return response.json()["image_url_or_b64"]
        except Exception as e:
            logger.error(f"BrainAPI Image Transform failed: {e}")
            raise

    def transform_video_to_anime(
        self, video_data: bytes, studio_style: str, prompt: str = ""
    ) -> str:
        try:
            vid_b64 = base64.b64encode(video_data).decode("utf-8")
            response = safe_http_request(
                "POST",
                f"{self.api_url}/video/transform/anime",
                json={"video": vid_b64, "studio_style": studio_style, "prompt": prompt},
                headers=self._get_headers(),
            )
            return response.json()["video_url_or_b64"]
        except Exception as e:
            logger.error(f"BrainAPI Video Transform failed: {e}")
            raise

    def generate_soundscape(
        self, video_metadata: Dict[str, Any], prompt: Optional[str] = None
    ) -> str:
        try:
            response = safe_http_request(
                "POST",
                f"{self.api_url}/audio/generate/soundscape",
                json={"video_metadata": video_metadata, "prompt": prompt},
                headers=self._get_headers(),
            )
            return response.json()["audio_url_or_b64"]
        except Exception as e:
            logger.error(f"BrainAPI Soundscape failed: {e}")
            raise

    def clone_voice(
        self, text: str, reference_audio: bytes, language: str = "fr"
    ) -> bytes:
        try:
            ref_b64 = base64.b64encode(reference_audio).decode("utf-8")
            response = safe_http_request(
                "POST",
                f"{self.api_url}/audio/clone-voice",
                json={"text": text, "reference_audio": ref_b64, "language": language},
                headers=self._get_headers(),
            )
            return base64.b64decode(response.json()["audio_b64"])
        except Exception as e:
            logger.error(f"BrainAPI Voice Cloning failed: {e}")
            raise

    def speech_to_speech(self, audio_input: bytes, system_prompt: str = "") -> bytes:
        try:
            aud_b64 = base64.b64encode(audio_input).decode("utf-8")
            response = safe_http_request(
                "POST",
                f"{self.api_url}/audio/speech-to-speech",
                json={"audio": aud_b64, "system_prompt": system_prompt},
                headers=self._get_headers(),
            )
            return base64.b64decode(response.json()["audio_b64"])
        except Exception as e:
            logger.error(f"BrainAPI Speech-to-Speech failed: {e}")
            raise

    def estimate_depth(self, image_data: bytes) -> bytes:
        try:
            img_b64 = base64.b64encode(image_data).decode("utf-8")
            response = safe_http_request(
                "POST",
                f"{self.api_url}/vision/depth",
                json={"image": img_b64},
                headers=self._get_headers(),
            )
            return base64.b64decode(response.json()["depth_b64"])
        except Exception as e:
            logger.error(f"BrainAPI Depth Estimation failed: {e}")
            raise

    def generate_3d_scene(
        self, image_data: bytes, depth_map: bytes, mode: str = "gaussian_splatting"
    ) -> Dict[str, Any]:
        try:
            img_b64 = base64.b64encode(image_data).decode("utf-8")
            depth_b64 = base64.b64encode(depth_map).decode("utf-8")
            response = safe_http_request(
                "POST",
                f"{self.api_url}/vision/generate-3d",
                json={"image": img_b64, "depth_map": depth_b64},
                headers=self._get_headers(),
            )
            return response.json()["scene_data"]
        except Exception as e:
            logger.error(f"BrainAPI 3D Generation failed: {e}")
            raise

    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]:
        try:
            img_b64 = base64.b64encode(image_data).decode("utf-8")
            response = safe_http_request(
                "POST",
                f"{self.api_url}/vision/manga/process",
                json={"image": img_b64},
                headers=self._get_headers(),
            )
            return response.json()
        except Exception as e:
            logger.error(f"BrainAPI Manga Processing failed: {e}")
            raise

    def translate_manga_page(
        self, image_data: bytes, target_lang: str = "Français"
    ) -> Dict[str, Any]:
        try:
            img_b64 = base64.b64encode(image_data).decode("utf-8")
            response = safe_http_request(
                "POST",
                f"{self.api_url}/vision/manga/translate",
                json={"image": img_b64, "target_lang": target_lang},
                headers=self._get_headers(),
            )
            return response.json()
        except Exception as e:
            logger.error(f"BrainAPI Manga Translation failed: {e}")
            raise

    def inpaint_text_bubbles(
        self, image_data: bytes, text_placements: List[Dict]
    ) -> str:
        try:
            img_b64 = base64.b64encode(image_data).decode("utf-8")
            response = safe_http_request(
                "POST",
                f"{self.api_url}/vision/manga/inpaint",
                json={"image": img_b64, "text_placements": text_placements},
                headers=self._get_headers(),
            )
            return response.json()["image_url_or_b64"]
        except Exception as e:
            logger.error(f"BrainAPI Manga In-painting failed: {e}")
            raise

    def generate_image_description(
        self,
        image_data: bytes,
        prompt: str = "Décris cette image d'anime de manière très détaillée.",
    ) -> str:
        try:
            img_b64 = base64.b64encode(image_data).decode("utf-8")
            response = safe_http_request(
                "POST",
                f"{self.api_url}/vision/describe",
                json={"image": img_b64, "prompt": prompt},
                headers=self._get_headers(),
            )
            return response.json()["description"]
        except Exception as e:
            logger.error(f"BrainAPI Image Description failed: {e}")
            raise

    def generate_video_description(
        self,
        video_data: bytes,
        prompt: str = "Décris cette vidéo d'anime de manière très détaillée.",
    ) -> str:
        try:
            vid_b64 = base64.b64encode(video_data).decode("utf-8")
            response = safe_http_request(
                "POST",
                f"{self.api_url}/video/describe",
                json={"video": vid_b64, "prompt": prompt},
                headers=self._get_headers(),
            )
            return response.json()["description"]
        except Exception as e:
            logger.error(f"BrainAPI Video Description failed: {e}")
            raise

    def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
        try:
            response = safe_http_request(
                "POST",
                f"{self.api_url}/v1/rerank",
                json={"query": query, "documents": documents},
                headers=self._get_headers(),
            )
            return response.json()["scores"]
        except Exception as e:
            logger.error(f"BrainAPI Document Rerank failed: {e}")
            raise

    def get_diagnostics(self, prompt: str, completion: str) -> Dict[str, Any]:
        try:
            response = safe_http_request(
                "POST",
                f"{self.api_url}/diagnostics",
                json={"prompt": prompt, "completion": completion},
                headers=self._get_headers(),
            )
            return response.json()["diagnostics"]
        except Exception as e:
            logger.error(f"BrainAPI Diagnostics failed: {e}")
            raise

    def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]:
        try:
            response = safe_http_request(
                "POST",
                f"{self.api_url}/uncertainty",
                json={"prompt": prompt, "completion": completion},
                headers=self._get_headers(),
            )
            return response.json()["uncertainty_metrics"]
        except Exception as e:
            logger.error(f"BrainAPI Uncertainty failed: {e}")
            raise

    def visual_rerank(
        self, query: str, image_urls: List[str], system_prompt: str = ""
    ) -> List[Dict[str, Any]]:
        try:
            response = safe_http_request(
                "POST",
                f"{self.api_url}/vision/rerank",
                json={
                    "query": query,
                    "image_urls": image_urls,
                    "system_prompt": system_prompt,
                },
                headers=self._get_headers(),
            )
            return response.json()["reranked_items"]
        except Exception as e:
            logger.error(f"BrainAPI Visual Rerank failed: {e}")
            raise

    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]:
        try:
            img_b64 = base64.b64encode(image_data).decode("utf-8")
            response = safe_http_request(
                "POST",
                f"{self.api_url}/vision/late-interaction",
                json={"image": img_b64},
                headers=self._get_headers(),
            )
            return response.json()["embeddings"]
        except Exception as e:
            logger.error(f"BrainAPI Late Interaction failed: {e}")
            raise

    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        try:
            response = safe_http_request(
                "POST",
                f"{self.api_url}/moderate",
                json={"text": text, "categories": categories},
                headers=self._get_headers(),
            )
            return response.json()["moderation"]
        except Exception as e:
            logger.error(f"BrainAPI Moderation failed: {e}")
            return super().moderate_content(text, categories)

    def health_check(self) -> dict:
        try:
            start_time = time.time()
            response = httpx.get(f"{self.api_url}/health", timeout=5.0)
            latency = (time.time() - start_time) * 1000
            return {
                "status": "online" if response.status_code == 200 else "degraded",
                "latency_ms": round(latency, 2),
                "engine": "BrainAPI",
            }
        except Exception:
            return {"status": "offline", "engine": "BrainAPI"}

    def generate_structured(
        self,
        prompt: str,
        response_model: type,
        system_prompt: str = "Tu es un expert en extraction de données structurées.",
        max_retries: int = 3,
    ) -> Any:
        """Brain API supporte nativement le JSON schema pour plus de précision."""
        try:
            # Si le serveur supporte nativement Pydantic/JSON Schema
            return super().generate_structured(
                prompt, response_model, system_prompt, max_retries
            )
        except Exception as e:
            logger.error(f"BrainAPI Structured Generation failed: {e}")
            raise
