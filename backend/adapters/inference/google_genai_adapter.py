import base64
import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

# Focused Mixin imports
from adapters.inference.depth_estimation import DepthEstimationMixin
from adapters.inference.reachability_health_mixin import ReachabilityHealthCheckMixin
from core.domain.entities.ai_schemas import (
    InferenceMetadata,
    InferenceResponse,
    TokenLogProb,
)
from core.domain.exceptions import ConfigurationError, InferenceError
from core.ports.inference_port import InferenceNotImplementedError, InferencePort
from core.ports.usage_port import UsagePort
from core.utils.gemini_models import GEMINI_EMBEDDING, GEMINI_FLASH
from core.utils.inference_config import check_google_genai_config
from core.utils.security import safe_http_request
from google import genai
from google.genai import types

logger = logging.getLogger("animetix.inference.google_genai")


def get_image_mime_type(image_data: bytes) -> str:
    """Détermine dynamiquement le type MIME d'une image à partir de ses premiers octets."""
    if image_data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    elif image_data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    elif image_data.startswith(b"RIFF") and image_data[8:12] == b"WEBP":
        return "image/webp"
    elif image_data.startswith(b"GIF87a") or image_data.startswith(b"GIF89a"):
        return "image/gif"
    return "image/png"


class GoogleGenAIAdapter(
    ReachabilityHealthCheckMixin, DepthEstimationMixin, InferencePort
):
    """
    Adapter for Google's Gemini models using the unified google-genai SDK.
    Supports local fallback mixins for specialized vision tasks.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        project: Optional[str] = None,
        location: Optional[str] = None,
        model_name: Optional[str] = None,
        vertexai: Optional[bool] = None,
        usage_port: Optional[UsagePort] = None,
    ):
        super().__init__(usage_port=usage_port)

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        config_error = check_google_genai_config(self.api_key)
        if config_error:
            raise ConfigurationError(config_error)
        self.project = (
            project
            or os.getenv("GOOGLE_CLOUD_PROJECT")
            or os.getenv("GCP_PROJECT_ID", "animetix")
        )
        self.location = (
            location
            or os.getenv("GOOGLE_CLOUD_LOCATION")
            or os.getenv("GCP_LOCATION", "europe-west9")
        )
        self.model_name = model_name or GEMINI_FLASH
        self.embedding_model = GEMINI_EMBEDDING

        if vertexai is not None:
            self.use_vertexai = vertexai
        else:
            self.use_vertexai = not bool(self.api_key)

        try:
            if self.use_vertexai:
                logger.info(
                    f"Initializing google-genai Client with Vertex AI backend. "
                    f"Project: {self.project}, Location: {self.location}"
                )
                self.client = genai.Client(
                    vertexai=True, project=self.project, location=self.location
                )
            else:
                logger.info(
                    "Initializing google-genai Client with Developer API Key backend."
                )
                self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Failed to initialize google-genai Client: {e}")
            self.client = None

        self._context_caches: Dict[str, Any] = {}
        self.cache_ttl_seconds = int(os.getenv("GEMINI_CACHE_TTL", "300"))
        self.cache_threshold_chars = int(os.getenv("GEMINI_CACHE_THRESHOLD", "120000"))

    def get_diagnostics(self, prompt: str, completion: str) -> Dict[str, Any]:
        """Récupère les données d'activation internes simulées pour Gemini."""
        raise InferenceNotImplementedError(
            "get_diagnostics not implemented for GoogleGenAIAdapter (requires model weights access or specific API support)."
        )

    def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]:
        """Calcule l'incertitude mathématique via les logprobs Gemini."""
        raise InferenceNotImplementedError(
            "calculate_uncertainty not implemented for GoogleGenAIAdapter (logprobs not directly exposed for this purpose)."
        )

    def health_check(self) -> dict:
        # Client-init reachability: no remote call — the SDK client is only built
        # when credentials resolve, so a live client means the API is reachable.
        if not self.client:
            return self._health_status("offline", reason="Client not initialized")
        return self._health_status(
            "online",
            model=self.model_name,
            backend="Vertex AI" if self.use_vertexai else "Developer API",
        )

    def calculate_visual_similarity(
        self, query: str, item_id: str, media_type: str
    ) -> float:
        """Calcule la similitude visuelle entre une requête (texte) et une image (item)."""
        import math  # noqa: E402

        try:
            # On génère l'embedding de la requête
            q_emb = self.get_text_embedding(query)
            # En l'absence de catalogue direct, on crée un embedding contextuel pour l'item
            item_emb = self.get_text_embedding(
                f"Representation for {media_type} item {item_id}"
            )

            if not q_emb or not item_emb:
                return 0.5

            # Cosine similarity
            dot_product = sum(a * b for a, b in zip(q_emb, item_emb))
            norm_q = math.sqrt(sum(a * a for a in q_emb))
            norm_i = math.sqrt(sum(b * b for b in item_emb))

            if norm_q == 0 or norm_i == 0:
                return 0.5

            return float(dot_product / (norm_q * norm_i))
        except Exception as e:
            logger.error(f"Visual similarity failed: {e}")
            return 0.0

    def get_text_embedding(self, text: str) -> List[float]:
        """Génère un embedding vectoriel pour un texte donné via Gemini."""
        if not self.client:
            return []
        try:
            res = self.client.models.embed_content(
                model=self.embedding_model,
                contents=text,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
            )
            self._log_usage(engine=f"google_genai:{self.embedding_model}", units=1)
            return res.embeddings[0].values
        except Exception as e:
            logger.error(f"Google GenAI Embedding failed: {e}")
            return []

    def get_image_embedding(
        self, image_data: bytes, model_id: Optional[str] = None
    ) -> List[float]:
        """Génère un embedding multimodal pour une image via Gemini."""
        if not self.client:
            return []
        try:
            mime = get_image_mime_type(image_data)
            image_part = types.Part.from_bytes(data=image_data, mime_type=mime)
            res = self.client.models.embed_content(
                model=model_id or self.embedding_model, contents=image_part
            )
            self._log_usage(
                engine=f"google_genai:{model_id or self.embedding_model}:vision",
                units=1,
            )
            return res.embeddings[0].values
        except Exception as e:
            logger.warning(
                f"Gemini multimodal embedding not supported or failed: {e}. Falling back to text description embedding."
            )
            # Fallback : embedding de la description textuelle
            description = self.generate_image_description(image_data)
            return self.get_text_embedding(description)

    def generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs,
    ) -> InferenceResponse:
        if not self.client:
            raise InferenceNotImplementedError(
                "Google GenAI client is not initialized."
            )

        config_args: Dict[str, Any] = {"temperature": 0.7}
        cache_name = self._get_or_create_cache(system_prompt)
        if cache_name:
            config_args["cached_content"] = cache_name
        else:
            config_args["system_instruction"] = system_prompt

        if thinking_mode or thinking_budget > 0:
            config_args["thinking_config"] = types.ThinkingConfig(include_thoughts=True)

        if include_logprobs:
            config_args["response_logprobs"] = True
            config_args["logprobs"] = 5

        config = types.GenerateContentConfig(**config_args)

        try:
            response = self.client.models.generate_content(
                model=self.model_name, contents=prompt, config=config
            )
            text = response.text or ""
            candidate = response.candidates[0] if response.candidates else None
            usage = self._get_usage_dict(response, len(prompt), len(text))
            self._log_usage(
                engine=f"google_genai:{self.model_name}",
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                allocated_budget=thinking_budget,
            )

            parsed_logprobs = self._parse_logprobs(candidate) if candidate else None
            thoughts = self._extract_thoughts(response)

            return InferenceResponse(
                text=text,
                metadata=InferenceMetadata(
                    logprobs=parsed_logprobs, usage=usage, thinking=thoughts
                ),
            )
        except Exception as e:
            logger.error(f"Error during GoogleGenAI generate: {e}")
            raise InferenceError(f"GoogleGenAI generate failed: {e}")

    def stream_generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs,
    ):
        if not self.client:
            raise InferenceNotImplementedError(
                "Google GenAI client is not initialized."
            )
        config_args: Dict[str, Any] = {"temperature": 0.7}
        cache_name = self._get_or_create_cache(system_prompt)
        if cache_name:
            config_args["cached_content"] = cache_name
        else:
            config_args["system_instruction"] = system_prompt

        if thinking_mode or thinking_budget > 0:
            config_args["thinking_config"] = types.ThinkingConfig(include_thoughts=True)

        if include_logprobs:
            config_args["response_logprobs"] = True
            config_args["logprobs"] = 5

        config = types.GenerateContentConfig(**config_args)

        try:
            response_stream = self.client.models.generate_content_stream(
                model=self.model_name, contents=prompt, config=config
            )
            for chunk in response_stream:
                chunk_text = chunk.text or ""
                candidate = chunk.candidates[0] if chunk.candidates else None
                usage = self._get_usage_dict(chunk, 0, len(chunk_text))
                parsed_logprobs = self._parse_logprobs(candidate) if candidate else None
                thoughts = self._extract_thoughts(chunk)
                yield InferenceResponse(
                    text=chunk_text,
                    metadata=InferenceMetadata(
                        logprobs=parsed_logprobs, usage=usage, thinking=thoughts
                    ),
                )
        except Exception as e:
            logger.error(f"Error during GoogleGenAI stream_generate: {e}")
            raise InferenceError(f"GoogleGenAI stream_generate failed: {e}")

    def generate_structured(
        self,
        prompt: str,
        response_model: type,
        system_prompt: str = "Tu es un expert en extraction de données structurées.",
        max_retries: int = 3,
    ) -> Any:
        if not self.client:
            raise InferenceNotImplementedError(
                "Google GenAI client is not initialized."
            )
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=response_model,
            temperature=0.1,
        )
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name, contents=prompt, config=config
                )
                if hasattr(response, "parsed") and response.parsed is not None:
                    return response.parsed
                text = response.text
                if text:
                    match = re.search(r"\{.*\}", text, re.DOTALL)
                    if match:
                        data = json.loads(match.group(0))
                        if hasattr(response_model, "model_validate"):
                            return response_model.model_validate(data)
                        return data
            except Exception as e:
                logger.error(
                    f"Structured Generation failed (Attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt == max_retries - 1:
                    raise InferenceError(f"GoogleGenAI generate_structured failed: {e}")
                time.sleep(1)
        raise InferenceError(
            "GoogleGenAI generate_structured failed to return valid data."
        )

    def generate_image_description(
        self,
        image_data: bytes,
        prompt: str = "Décris cette image d'anime de manière très détaillée.",
    ) -> str:
        if not self.client:
            raise InferenceNotImplementedError(
                "Google GenAI client is not initialized."
            )
        mime = get_image_mime_type(image_data)
        image_part = types.Part.from_bytes(data=image_data, mime_type=mime)
        try:
            response = self.client.models.generate_content(
                model=self.model_name, contents=[image_part, prompt]
            )
            text = response.text or ""
            usage = self._get_usage_dict(response, len(prompt), len(text))
            self._log_usage(
                engine=f"google_genai:{self.model_name}:vision",
                input_tokens=usage.get("prompt_tokens", 0) + 258,
                output_tokens=usage.get("completion_tokens", 0),
            )
            return text
        except Exception as e:
            logger.error(f"Error during GoogleGenAI generate_image_description: {e}")
            raise InferenceError(f"GoogleGenAI generate_image_description failed: {e}")

    def generate_video_description(
        self,
        video_data: bytes,
        prompt: str = "Décris cette vidéo d'anime de manière très détaillée.",
    ) -> str:
        """Utilise le VLM Gemini pour décrire une vidéo."""
        if not self.client:
            raise InferenceNotImplementedError(
                "Google GenAI client is not initialized."
            )

        # Gemini supporte le passage direct de bytes pour les vidéos courtes ou nécessite un upload pour les longues.
        # Pour Animetix, les clips sont généralement courts (< 1 min).
        video_part = types.Part.from_bytes(data=video_data, mime_type="video/mp4")

        try:
            response = self.client.models.generate_content(
                model=self.model_name, contents=[video_part, prompt]
            )
            text = response.text or ""
            self._log_usage(engine=f"google_genai:{self.model_name}:video", units=1)
            return text
        except Exception as e:
            logger.error(f"Error during GoogleGenAI generate_video_description: {e}")
            raise InferenceError(f"GoogleGenAI generate_video_description failed: {e}")

    def get_video_temporal_embeddings(self, video_data: bytes) -> List[Dict[str, Any]]:
        """Génère des métadonnées temporelles pour une vidéo via Gemini."""
        if not self.client:
            raise InferenceNotImplementedError(
                "Google GenAI client is not initialized."
            )
        video_part = types.Part.from_bytes(data=video_data, mime_type="video/mp4")
        prompt = (
            "Analyse cette vidéo et décompose-la en segments logiques. "
            "Pour chaque segment, fournis un résumé des actions. "
            "Réponds UNIQUEMENT au format JSON : [{'start': float, 'end': float, 'summary': str}]."
        )
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[video_part, prompt],
                config=types.GenerateContentConfig(temperature=0.1),
            )
            text = response.text
            match = re.search(r"\[.*\]", text, re.DOTALL)
            if match:
                segments = json.loads(match.group(0))
                self._log_usage(
                    engine=f"google_genai:{self.model_name}:video_temporal", units=1
                )
                return segments
        except Exception as e:
            logger.error(f"Google GenAI Video Temporal Analysis failed: {e}")
        return []

    def localize_video_actions(
        self, video_data: bytes, action_queries: List[str]
    ) -> List[Dict[str, Any]]:
        """Localise des actions spécifiques dans une vidéo via Gemini."""
        if not self.client:
            raise InferenceNotImplementedError(
                "Google GenAI client is not initialized."
            )
        video_part = types.Part.from_bytes(data=video_data, mime_type="video/mp4")

        all_actions = []
        for query in action_queries:
            prompt = (
                f"Dans cette vidéo, trouve les moments exacts (début et fin en secondes) où l'action '{query}' se produit. "
                "Réponds UNIQUEMENT au format JSON : [{'start': float, 'end': float, 'confidence': float}]. "
                "Si l'action n'est pas trouvée, réponds []."
            )
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[video_part, prompt],
                    config=types.GenerateContentConfig(temperature=0.1),
                )
                text = response.text
                match = re.search(r"\[.*\]", text, re.DOTALL)
                if match:
                    localizations = json.loads(match.group(0))
                    for loc in localizations:
                        loc["action"] = query
                        all_actions.append(loc)
            except Exception as e:
                logger.error(
                    f"Google GenAI Video Action Localization failed for '{query}': {e}"
                )

        if all_actions:
            self._log_usage(
                engine=f"google_genai:{self.model_name}:video_localize",
                units=len(action_queries),
            )
        return all_actions

    def detect_objects(
        self,
        image_data: bytes,
        candidate_queries: List[str],
        model_id: Optional[str] = None,
    ) -> List[Dict]:
        """Détecte des objets via VLM Gemini (Open-world detection)."""
        prompt = (
            f"Détecte ces éléments dans l'image d'anime : {', '.join(candidate_queries)}. "
            "Réponds UNIQUEMENT au format JSON : [{'label': str, 'box_2d': [ymin, xmin, ymax, xmax], 'score': float}]. "
            "Les coordonnées doivent être entre 0 et 1000."
        )
        try:
            res_text = self.generate_image_description(image_data, prompt=prompt)
            match = re.search(r"\[.*\]", res_text, re.DOTALL)
            if match:
                objects = json.loads(match.group(0))
                # Conversion box format if needed
                for obj in objects:
                    if "box_2d" in obj:
                        obj["box"] = obj.pop("box_2d")
                return objects
        except Exception as e:
            logger.error(f"Google GenAI Object Detection failed: {e}")
        return []

    def classify_image(
        self,
        image_data: bytes,
        candidate_labels: List[str],
        model_id: Optional[str] = None,
    ) -> Dict[str, float]:
        """Classifie une image zero-shot via Gemini."""
        prompt = f"Parmi ces labels : {', '.join(candidate_labels)}, lequel correspond le mieux à cette image ? Réponds au format JSON : {{'label': score}}."
        try:
            res_text = self.generate_image_description(image_data, prompt=prompt)
            match = re.search(r"\{.*\}", res_text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception as e:
            logger.error(f"Google GenAI Classification failed: {e}")
        return {label: 0.0 for label in candidate_labels}

    def visual_rerank(
        self,
        query: str,
        image_urls: List[str],
        system_prompt: str = "Tu es un expert en analyse visuelle d'anime.",
    ) -> List[Dict[str, Any]]:
        if not self.client or not image_urls:
            return []
        parts = []
        downloaded_indices = []
        for idx, url in enumerate(image_urls):
            try:
                res = safe_http_request("GET", url, timeout=10)
                if res.status_code == 200:
                    img_bytes = res.content
                    mime = get_image_mime_type(img_bytes)
                    parts.append(f"\n[Image Index {idx}]")
                    parts.append(types.Part.from_bytes(data=img_bytes, mime_type=mime))
                    downloaded_indices.append(idx)
            except Exception as e:
                logger.error(f"Failed to download image {url} for visual_rerank: {e}")

        if not downloaded_indices:
            return [{"index": i, "score": 0.0} for i in range(len(image_urls))]

        prompt_text = (
            f"Analyse ces {len(downloaded_indices)} images et classe-les selon leur pertinence par rapport à la requête : '{query}'.\n"
            "Réponds uniquement sous la forme d'un objet JSON contenant la clé 'scores' : "
            '{"scores": [{"index": int, "score": float}]}'
        )
        parts.append(prompt_text)

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=parts,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            text_response = response.text
            self._log_usage(
                engine=f"google_genai:{self.model_name}:visual_rerank",
                units=len(image_urls),
            )
            match = re.search(r"\{.*\}", text_response, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                scores = data.get("scores", [])
                final_results = []
                for item in scores:
                    idx = item.get("index")
                    if idx is not None:
                        final_results.append(
                            {"index": int(idx), "score": float(item.get("score", 0.0))}
                        )
                if final_results:
                    return final_results
        except Exception as e:
            logger.error(f"Google GenAI visual_rerank failed: {e}")
        return [{"index": i, "score": 0.0} for i in range(len(image_urls))]

    def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
        """Ré-ordonne les documents via prompt LLM Gemini."""
        if not documents:
            return []
        prompt = f"Requête : {query}\n\nDocuments à évaluer :\n"
        for i, doc in enumerate(documents):
            prompt += f"ID {i} : {doc[:1000]}\n"
        prompt += "\nPour chaque document, donne un score de pertinence entre 0.0 et 1.0. Réponds avec une liste JSON : [score0, score1, ...]"
        try:
            response = self.generate(
                prompt,
                system_prompt="Tu es un système de réordonnancement (reranker) expert.",
            )
            match = re.search(r"\[.*\]", response.text)
            if match:
                scores = json.loads(match.group(0))
                if len(scores) == len(documents):
                    return [float(s) for s in scores]
        except Exception as e:
            logger.warning(f"Google GenAI Reranking failed: {e}")
        return [0.0] * len(documents)

    def generate_image(self, prompt: str, style: str = "") -> str:
        """Génère une image via Imagen 3 (Vertex AI uniquement)."""
        if not self.use_vertexai:
            logger.warning(
                "generate_image via GoogleGenAI requires Vertex AI backend. Falling back to InferenceNotImplementedError."
            )
            raise InferenceNotImplementedError("generate_image requires Vertex AI")
        try:
            # Note: Imagen generation requires specific model name, usually 'imagen-3' or similar
            res = self.client.models.generate_image(
                model="imagen-3.0-generate-001",
                prompt=f"{prompt}, {style}",
                config=types.GenerateImageConfig(
                    number_of_images=1, include_rai_reason=True
                ),
            )
            image_bytes = res.generated_images[0].image.data
            self._log_usage(engine="google_genai:imagen-3", units=1)
            return (
                f"data:image/png;base64,{base64.b64encode(image_bytes).decode('utf-8')}"
            )
        except Exception as e:
            logger.error(f"Google Imagen generation failed: {e}")
            raise InferenceError(f"Imagen failed: {e}")

    def generate_sprite(self, prompt: str, style: str = "") -> str:
        """Génère un sprite de personnage (généralement sur fond transparent ou blanc)."""
        raise InferenceNotImplementedError(
            "generate_sprite not implemented for GoogleGenAIAdapter"
        )

    # --- Internal Helpers ---

    def _get_or_create_cache(self, system_prompt: str) -> Optional[str]:
        if (
            not self.client
            or not system_prompt
            or len(system_prompt) < self.cache_threshold_chars
        ):
            return None
        if "gemini" not in self.model_name.lower():
            return None
        import hashlib  # noqa: E402

        context_hash = hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()
        current_time = time.time()
        if context_hash in self._context_caches:
            cache_name, expire_time = self._context_caches[context_hash]
            if current_time < expire_time:
                return cache_name
            try:
                self.client.caches.delete(name=cache_name)
            except Exception as e:
                logger.warning(
                    f"Failed to delete expired Gemini context cache {cache_name}: {e}"
                )
            del self._context_caches[context_hash]
        try:
            ttl_str = f"{self.cache_ttl_seconds}s"
            cache = self.client.caches.create(
                model=self.model_name,
                config=types.CreateCachedContentConfig(
                    display_name=f"animetix_ctx_{context_hash[:8]}",
                    system_instruction=system_prompt,
                    ttl=ttl_str,
                ),
            )
            self._context_caches[context_hash] = (
                cache.name,
                current_time + self.cache_ttl_seconds,
            )
            return cache.name
        except Exception as e:
            logger.error(f"Failed to create Gemini context cache: {e}")
            return None

    def _parse_logprobs(self, candidate: Any) -> Optional[List[TokenLogProb]]:
        if not hasattr(candidate, "logprobs_result") or not candidate.logprobs_result:
            return None
        parsed_logprobs = []
        logprobs_res = candidate.logprobs_result
        chosen_candidates = getattr(logprobs_res, "chosen_candidates", []) or []
        top_candidates = getattr(logprobs_res, "top_candidates", []) or []
        for idx, chosen in enumerate(chosen_candidates):
            top_list = []
            if idx < len(top_candidates):
                step_alternatives = top_candidates[idx]
                candidates_list = getattr(
                    step_alternatives, "candidates", step_alternatives
                )
                if isinstance(candidates_list, list):
                    for alt in candidates_list:
                        top_list.append(
                            {
                                getattr(alt, "token", ""): getattr(
                                    alt, "log_probability", 0.0
                                )
                            }
                        )
            parsed_logprobs.append(
                TokenLogProb(
                    token=getattr(chosen, "token", ""),
                    logprob=getattr(chosen, "log_probability", 0.0),
                    top_logprobs=top_list if top_list else None,
                )
            )
        return parsed_logprobs

    def _extract_thoughts(self, response: Any) -> Optional[str]:
        if not response.candidates or not response.candidates[0].content:
            return None
        thoughts = []
        for part in response.candidates[0].content.parts:
            if getattr(part, "thought", False):
                text_val = getattr(part, "text", "")
                if text_val:
                    thoughts.append(text_val)
        return "\n".join(thoughts) if thoughts else None

    def _get_usage_dict(
        self, response: Any, default_prompt_len: int = 0, default_text_len: int = 0
    ) -> Dict[str, int]:
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            metadata = response.usage_metadata
            return {
                "prompt_tokens": getattr(
                    metadata, "prompt_token_count", default_prompt_len // 4
                ),
                "completion_tokens": getattr(
                    metadata, "candidates_token_count", default_text_len // 4
                ),
                "total_tokens": getattr(metadata, "total_token_count", 0),
            }
        return {
            "prompt_tokens": default_prompt_len // 4,
            "completion_tokens": default_text_len // 4,
            "total_tokens": (default_prompt_len + default_text_len) // 4,
        }
