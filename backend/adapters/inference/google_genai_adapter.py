import os
import time
import logging
from typing import Optional, List, Dict, Any
from google import genai
from google.genai import types

from core.ports.inference_port import InferencePort, InferenceNotImplementedError
from core.ports.usage_port import UsagePort
from core.domain.entities.ai_schemas import InferenceResponse, InferenceMetadata, TokenLogProb
from core.utils.security import is_safe_url, safe_http_request
from core.domain.exceptions import InferenceError

logger = logging.getLogger("animetix.inference.google_genai")

def get_image_mime_type(image_data: bytes) -> str:
    """Détermine dynamiquement le type MIME d'une image à partir de ses premiers octets."""
    if image_data.startswith(b'\x89PNG\r\n\x1a\n'):
        return "image/png"
    elif image_data.startswith(b'\xff\xd8\xff'):
        return "image/jpeg"
    elif image_data.startswith(b'RIFF') and image_data[8:12] == b'WEBP':
        return "image/webp"
    elif image_data.startswith(b'GIF87a') or image_data.startswith(b'GIF89a'):
        return "image/gif"
    return "image/png"


class GoogleGenAIAdapter(InferencePort):
    """
    Adapter for Google's Gemini models using the unified google-genai SDK.
    Supports both direct Gemini Developer API and Vertex AI (Gemini Enterprise Agent Platform).
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        project: Optional[str] = None,
        location: Optional[str] = None,
        model_name: Optional[str] = None,
        vertexai: Optional[bool] = None,
        usage_port: Optional[UsagePort] = None
    ):
        super().__init__(usage_port=usage_port)
        
        # Récupération des configurations via paramètres ou variables d'environnement
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.project = project or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID", "animetix")
        self.location = location or os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("GCP_LOCATION", "europe-west9")
        self.model_name = model_name or os.getenv("GEMINI_MODEL_NAME") or "gemini-3.5-flash"
        
        # Choix automatique du mode d'authentification
        if vertexai is not None:
            self.use_vertexai = vertexai
        else:
            # S'il n'y a pas de clé d'API développeur, on bascule vers Vertex AI ADC par défaut
            self.use_vertexai = not bool(self.api_key)
            
        try:
            if self.use_vertexai:
                logger.info(
                    f"Initializing google-genai Client with Vertex AI backend. "
                    f"Project: {self.project}, Location: {self.location}"
                )
                self.client = genai.Client(
                    vertexai=True,
                    project=self.project,
                    location=self.location
                )
            else:
                logger.info("Initializing google-genai Client with Developer API Key backend.")
                self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Failed to initialize google-genai Client: {e}")
            self.client = None
            
        self._context_caches = {}
        self.cache_ttl_seconds = int(os.getenv("GEMINI_CACHE_TTL", "300"))
        self.cache_threshold_chars = int(os.getenv("GEMINI_CACHE_THRESHOLD", "120000"))

    def health_check(self) -> dict:
        """Vérifie l'état de l'unité de calcul."""
        if not self.client:
            return {"status": "offline", "reason": "Client not initialized"}
        return {
            "status": "online",
            "model": self.model_name,
            "backend": "Vertex AI" if self.use_vertexai else "Developer API"
        }

    def _parse_logprobs(self, candidate: Any) -> Optional[List[TokenLogProb]]:
        """Extrait et formate les logprobs à partir du candidat de réponse."""
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
                candidates_list = getattr(step_alternatives, "candidates", step_alternatives)
                if isinstance(candidates_list, list):
                    for alt in candidates_list:
                        token_str = getattr(alt, "token", "")
                        prob_val = getattr(alt, "log_probability", 0.0)
                        top_list.append({token_str: prob_val})
            
            parsed_logprobs.append(TokenLogProb(
                token=getattr(chosen, "token", ""),
                logprob=getattr(chosen, "log_probability", 0.0),
                top_logprobs=top_list if top_list else None
            ))
            
        return parsed_logprobs

    def _extract_thoughts(self, response: Any) -> Optional[str]:
        """Extrait les pensées internes (thought) retournées par le modèle."""
        if not response.candidates or not response.candidates[0].content:
            return None
            
        thoughts = []
        for part in response.candidates[0].content.parts:
            if getattr(part, "thought", False):
                text_val = getattr(part, "text", "")
                if text_val:
                    thoughts.append(text_val)
                    
        return "\n".join(thoughts) if thoughts else None

    def _get_usage_dict(self, response: Any, default_prompt_len: int = 0, default_text_len: int = 0) -> Dict[str, int]:
        """Formate les informations de consommation sous forme de dictionnaire."""
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            metadata = response.usage_metadata
            return {
                "prompt_tokens": getattr(metadata, "prompt_token_count", default_prompt_len // 4),
                "completion_tokens": getattr(metadata, "candidates_token_count", default_text_len // 4),
                "total_tokens": getattr(metadata, "total_token_count", 0)
            }
        return {
            "prompt_tokens": default_prompt_len // 4,
            "completion_tokens": default_text_len // 4,
            "total_tokens": (default_prompt_len + default_text_len) // 4
        }

    def _get_or_create_cache(self, system_prompt: str) -> Optional[str]:
        """Gère la création et la réutilisation de cache de contexte sur Vertex AI / Gemini."""
        if not self.client or not system_prompt:
            return None
            
        # Le cache de contexte n'est supporté que sur les modèles Gemini
        if "gemini" not in self.model_name.lower():
            return None
            
        if len(system_prompt) < self.cache_threshold_chars:
            return None
            
        import hashlib
        import time
        
        context_hash = hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()
        current_time = time.time()
        
        if context_hash in self._context_caches:
            cache_name, expire_time = self._context_caches[context_hash]
            if current_time < expire_time:
                logger.debug(f"Reusing existing context cache: {cache_name}")
                return cache_name
            else:
                # Supprimer le cache expiré
                try:
                    self.client.caches.delete(name=cache_name)
                    logger.debug(f"Deleted expired context cache: {cache_name}")
                except Exception as e:
                    logger.warning(f"Failed to delete expired remote cache {cache_name}: {e}")
                del self._context_caches[context_hash]
                
        try:
            logger.info(
                f"Creating new context cache on Gemini/Vertex AI for prompt of length {len(system_prompt)} characters..."
            )
            ttl_str = f"{self.cache_ttl_seconds}s"
            cache_config = types.CreateCachedContentConfig(
                display_name=f"animetix_ctx_{context_hash[:8]}",
                system_instruction=system_prompt,
                ttl=ttl_str
            )
            cache = self.client.caches.create(
                model=self.model_name,
                config=cache_config
            )
            expire_time = current_time + self.cache_ttl_seconds
            self._context_caches[context_hash] = (cache.name, expire_time)
            logger.info(f"Successfully created context cache: {cache.name} (TTL: {ttl_str})")
            return cache.name
        except Exception as e:
            logger.error(f"Failed to create Gemini context cache: {e}")
            return None

    def generate(
        self, 
        prompt: str, 
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False
    ) -> InferenceResponse:
        if not self.client:
            raise InferenceNotImplementedError("Google GenAI client is not initialized.")
            
        # Configuration des paramètres de génération
        config_args = {
            "temperature": 0.7
        }
        
        # Gestion du cache de contexte
        cache_name = self._get_or_create_cache(system_prompt)
        if cache_name:
            config_args["cached_content"] = cache_name
        else:
            config_args["system_instruction"] = system_prompt
        
        # Gestion du mode raisonnement (thinking)
        if thinking_mode or thinking_budget > 0:
            if "3." in self.model_name:
                config_args["thinking_config"] = types.ThinkingConfig(thinking_level="HIGH")
            else:
                budget = thinking_budget if thinking_budget > 0 else -1
                config_args["thinking_config"] = types.ThinkingConfig(thinking_budget=budget)
                
        # Gestion des logprobs
        if include_logprobs:
            config_args["response_logprobs"] = True
            config_args["logprobs"] = 5
            
        config = types.GenerateContentConfig(**config_args)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            
            text = response.text or ""
            candidate = response.candidates[0] if response.candidates else None
            
            # Log usage
            usage = self._get_usage_dict(response, len(prompt), len(text))
            self._log_usage(
                engine=f"google_genai:{self.model_name}",
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0)
            )
            
            # Parsing logprobs et thoughts
            parsed_logprobs = self._parse_logprobs(candidate) if candidate else None
            thoughts = self._extract_thoughts(response)
            
            return InferenceResponse(
                text=text,
                metadata=InferenceMetadata(
                    logprobs=parsed_logprobs,
                    usage=usage,
                    thinking=thoughts
                )
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
        include_logprobs: bool = False
    ):
        if not self.client:
            raise InferenceNotImplementedError("Google GenAI client is not initialized.")
            
        config_args = {
            "temperature": 0.7
        }
        
        # Gestion du cache de contexte
        cache_name = self._get_or_create_cache(system_prompt)
        if cache_name:
            config_args["cached_content"] = cache_name
        else:
            config_args["system_instruction"] = system_prompt
        
        if thinking_mode or thinking_budget > 0:
            if "3." in self.model_name:
                config_args["thinking_config"] = types.ThinkingConfig(thinking_level="HIGH")
            else:
                budget = thinking_budget if thinking_budget > 0 else -1
                config_args["thinking_config"] = types.ThinkingConfig(thinking_budget=budget)
                
        if include_logprobs:
            config_args["response_logprobs"] = True
            config_args["logprobs"] = 5
            
        config = types.GenerateContentConfig(**config_args)
        
        try:
            response_stream = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=prompt,
                config=config
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
                        logprobs=parsed_logprobs,
                        usage=usage,
                        thinking=thoughts
                    )
                )
        except Exception as e:
            logger.error(f"Error during GoogleGenAI stream_generate: {e}")
            raise InferenceError(f"GoogleGenAI stream_generate failed: {e}")

    def generate_structured(
        self, 
        prompt: str, 
        response_model: type,
        system_prompt: str = "Tu es un expert en extraction de données structurées.",
        max_retries: int = 3
    ) -> Any:
        if not self.client:
            raise InferenceNotImplementedError("Google GenAI client is not initialized.")
            
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=response_model,
            temperature=0.1
        )
        
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config
                )
                
                # Le SDK parse automatiquement l'objet JSON en instance Pydantic
                if hasattr(response, "parsed") and response.parsed is not None:
                    return response.parsed
                    
                # Repli en cas de non-présence du champ parsed
                text = response.text
                if text:
                    import json
                    import re
                    match = re.search(r'\{.*\}', text, re.DOTALL)
                    if match:
                        data = json.loads(match.group(0))
                        if hasattr(response_model, "model_validate"):
                            return response_model.model_validate(data)
                        return data
            except Exception as e:
                logger.error(f"Structured Generation failed (Attempt {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise InferenceError(f"GoogleGenAI generate_structured failed: {e}")
                time.sleep(1)
                
        raise InferenceError("GoogleGenAI generate_structured failed to return valid data.")

    def generate_image_description(
        self, 
        image_data: bytes, 
        prompt: str = "Décris cette image d'anime de manière très détaillée."
    ) -> str:
        """Utilise le VLM Gemini pour décrire une image d'anime."""
        if not self.client:
            raise InferenceNotImplementedError("Google GenAI client is not initialized.")
            
        mime = get_image_mime_type(image_data)
        image_part = types.Part.from_bytes(data=image_data, mime_type=mime)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[image_part, prompt]
            )
            text = response.text or ""
            
            # Log usage
            usage = self._get_usage_dict(response, len(prompt), len(text))
            self._log_usage(
                engine=f"google_genai:{self.model_name}:vision",
                input_tokens=usage.get("prompt_tokens", 0) + 258, # approximation pour l'image
                output_tokens=usage.get("completion_tokens", 0)
            )
            return text
        except Exception as e:
            logger.error(f"Error during GoogleGenAI generate_image_description: {e}")
            raise InferenceError(f"GoogleGenAI generate_image_description failed: {e}")

    def visual_rerank(
        self, 
        query: str, 
        image_urls: List[str], 
        system_prompt: str = "Tu es un expert en analyse visuelle d'anime."
    ) -> List[Dict[str, Any]]:
        """Classe les images fournies par pertinence par rapport à une requête textuelle."""
        if not self.client or not image_urls:
            return []
            
        import json
        import re
        
        # 1. Téléchargement sécurisé des images en mémoire
        parts = []
        downloaded_indices = []
        for idx, url in enumerate(image_urls):
            try:
                # safe_http_request pour se prémunir des attaques SSRF
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
            logger.warning("No image URLs could be downloaded for visual_rerank. Returning uniform scores.")
            return [{"index": i, "score": 1.0 / len(image_urls)} for i in range(len(image_urls))]
            
        # 2. Construction du prompt d'évaluation
        prompt_text = (
            f"Analyse ces {len(downloaded_indices)} images et classe-les selon leur pertinence "
            f"par rapport à la requête suivante : '{query}'.\n"
            "Réponds uniquement sous la forme d'un objet JSON valide contenant la clé 'scores' : "
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
                    temperature=0.1
                )
            )
            
            text_response = response.text
            self._log_usage(engine=f"google_genai:{self.model_name}:visual_rerank", units=len(image_urls))
            
            # Extraction JSON robuste
            match = re.search(r'\{.*\}', text_response, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                scores = data.get("scores", [])
                final_results = []
                for item in scores:
                    idx = item.get("index")
                    if idx is not None:
                        final_results.append({
                            "index": int(idx),
                            "score": float(item.get("score", 0.0))
                        })
                if final_results:
                    return final_results
        except Exception as e:
            logger.error(f"Google GenAI visual_rerank failed: {e}")
            
        # Fallback uniforme par défaut
        return [{"index": i, "score": 0.0} for i in range(len(image_urls))]
