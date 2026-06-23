import logging
import time
from typing import Any, Dict, List, Optional

from adapters.inference.capability_registry import CapabilityRegistry
from core.domain.entities.ai_schemas import InferenceResponse, TokenLogProb
from core.ports.inference_port import InferenceNotImplementedError, InferencePort

logger = logging.getLogger("animetix.inference.fallback")


class FallbackInferenceAdapter(InferencePort):
    """
    Orchestre une liste d'adaptateurs d'inférence.
    Passe au suivant si l'un d'eux lève une exception ou retourne une réponse
    marquée comme échec via la sentinelle typée ``InferenceResponse.is_error``.
    Inclut un mécanisme de monitoring via ObservabilityService.
    """

    def __init__(
        self, adapters: List[InferencePort], obs_service: Optional[Any] = None
    ):
        self.adapters = [a for a in adapters if a is not None]
        self.obs_service = obs_service
        self._online_adapters: set[InferencePort] = set()

        # Cache for diagnostics & advanced uncertainty
        self._last_completion: Optional[str] = None
        self._last_logprobs: Optional[List[TokenLogProb]] = None

        self._check_initial_health()
        self._capabilities = CapabilityRegistry(self.adapters)

    def _check_initial_health(self) -> None:
        for adapter in self.adapters:
            try:
                if hasattr(adapter, "health_check"):
                    status = adapter.health_check()
                    if status.get("status") == "online":
                        self._online_adapters.add(adapter)
                else:
                    self._online_adapters.add(adapter)
            except Exception as e:
                logger.warning(
                    f"Health check failed for adapter {adapter.__class__.__name__}: {e}"
                )
        # Si tous sont offline (ex: tests hors ligne), on les autorise tous par sécurité
        if not self._online_adapters:
            self._online_adapters.update(self.adapters)

    def _get_ordered_adapters(
        self, adapters: List[InferencePort]
    ) -> List[InferencePort]:
        # Tente d'abord les adaptateurs en ligne, puis les autres en dernier recours
        online = [a for a in adapters if a in self._online_adapters]
        offline = [a for a in adapters if a not in self._online_adapters]
        return online + offline

    def _report_failure(
        self,
        adapter: InferencePort,
        method: str,
        error: str,
        latency: float,
        prompt_hint: str = "",
    ):
        """Helper centralisé pour le logging et le monitoring des échecs."""
        adapter_name = adapter.__class__.__name__
        error_msg = f"❌ [Fallback] {adapter_name}.{method} failed after {latency:.2f}s: {error}"
        if prompt_hint:
            error_msg += f" | Prompt hint: {prompt_hint[:50]}..."

        logger.error(error_msg)

        if self.obs_service:
            self.obs_service.log_error(
                error_type="InferenceAdapterFailure",
                message=f"{adapter_name}.{method}: {error}",
            )
            # On log aussi les métriques d'échec
            self.obs_service.log_inference(
                model_id=adapter_name,
                latency=latency,
                tokens=0,
                metadata={"status": "failed", "method": method, "error": error[:100]},
            )

    def generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs,
    ) -> InferenceResponse:
        last_error = ""
        capable_adapters = self._capabilities.for_method("generate")
        if not capable_adapters:
            capable_adapters = self.adapters

        ordered_adapters = self._get_ordered_adapters(capable_adapters)
        for adapter in ordered_adapters:
            if not hasattr(adapter, "generate") or not callable(
                getattr(adapter, "generate")
            ):
                continue
            adapter_name = adapter.__class__.__name__
            start_time = time.time()
            try:
                logger.info(f"🔄 [Fallback] Trying {adapter_name}...")

                # Signature check for backward compatibility (optional but safer)
                import inspect  # noqa: E402

                sig = inspect.signature(adapter.generate)
                call_kwargs: Dict[str, Any] = {
                    "thinking_budget": thinking_budget,
                    "thinking_mode": thinking_mode,
                }
                if "include_logprobs" in sig.parameters:
                    call_kwargs["include_logprobs"] = include_logprobs
                call_kwargs.update(kwargs)

                result = adapter.generate(prompt, system_prompt, **call_kwargs)
                latency = time.time() - start_time

                # Échec doux : résultat nul ou réponse marquée via la sentinelle is_error.
                if not result or result.is_error:
                    last_error = result.text if result else "Résultat vide"
                    self._report_failure(
                        adapter, "generate", last_error, latency, prompt
                    )
                    continue  # On passe au suivant

                # Si on est ici, on a un succès !
                logger.info(f"✅ [Fallback] {adapter_name} success in {latency:.2f}s!")
                self._last_completion = result.text
                self._last_logprobs = (
                    result.metadata.logprobs if result.metadata else None
                )
                if self.obs_service:
                    total_tokens = (
                        result.metadata.usage.get("total_tokens", 0)
                        if result.metadata.usage
                        else len(result.text) // 4
                    )
                    self.obs_service.log_inference(
                        model_id=adapter_name, latency=latency, tokens=total_tokens
                    )
                return result

            except Exception as e:
                latency = time.time() - start_time
                last_error = str(e)
                self._report_failure(
                    adapter, "generate", f"CRASH: {last_error}", latency, prompt
                )
                continue

        return InferenceResponse.failure(
            f"Échec critique : Tous les moteurs LLM ont échoué. Dernière erreur: {last_error}"
        )

    def stream_generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs,
    ):
        """Streaming avec repli intelligent."""
        capable_adapters = self._capabilities.for_method("stream_generate")
        if not capable_adapters:
            capable_adapters = self.adapters

        ordered_adapters = self._get_ordered_adapters(capable_adapters)
        for adapter in ordered_adapters:
            if not hasattr(adapter, "stream_generate") or not callable(
                getattr(adapter, "stream_generate")
            ):
                continue
            start_time = time.time()
            try:
                # Signature check for backward compatibility
                import inspect  # noqa: E402

                sig = inspect.signature(adapter.stream_generate)
                call_kwargs: Dict[str, Any] = {
                    "thinking_budget": thinking_budget,
                    "thinking_mode": thinking_mode,
                }
                if "include_logprobs" in sig.parameters:
                    call_kwargs["include_logprobs"] = include_logprobs
                call_kwargs.update(kwargs)

                # Tentative de premier token pour valider l'adaptateur
                gen = adapter.stream_generate(prompt, system_prompt, **call_kwargs)
                first_chunk = next(gen)
                latency = time.time() - start_time

                # Validation du premier chunk (InferenceResponse)
                if first_chunk and not first_chunk.is_error:

                    def success_gen():
                        yield first_chunk
                        yield from gen

                    logger.info(
                        f"✅ [Stream Fallback] {adapter.__class__.__name__} success in {latency:.2f}s"
                    )
                    return success_gen()

                error_hint = first_chunk.text if first_chunk else "Premier chunk vide"
                self._report_failure(
                    adapter, "stream_generate", error_hint, latency, prompt
                )
            except StopIteration:
                self._report_failure(
                    adapter,
                    "stream_generate",
                    "StopIteration (Pas de réponse)",
                    time.time() - start_time,
                    prompt,
                )
                continue
            except Exception as e:
                self._report_failure(
                    adapter,
                    "stream_generate",
                    f"CRASH: {str(e)}",
                    time.time() - start_time,
                    prompt,
                )
                continue

        # Fallback final vers generate standard (qui a sa propre logique de repli)
        def error_gen():
            yield self.generate(
                prompt, system_prompt, thinking_budget, thinking_mode, include_logprobs
            )

        return error_gen()

    def generate_image(self, prompt: str, style: str = "") -> str:
        """Génère une image avec repli."""
        from django.core.cache import cache

        budget_exceeded = cache.get("paid_api_budget_exceeded", False)

        if budget_exceeded:
            logger.info(
                "💸 Paid API budget exceeded! Routing image generation to self-hosted worker."
            )
            return self._generate_image_via_worker(prompt, style)

        # Otherwise, try the standard fallback orchestrator chain (paid APIs first)
        try:
            res = self._fallback_call("generate_image", prompt, style)
            if res:
                return res
            logger.warning(
                "Paid API returned empty result. Triggering failover to self-hosted worker."
            )
        except Exception as e:
            logger.warning(
                f"Paid API failed: {e}. Triggering failover to self-hosted worker."
            )
            cache.set("paid_api_failover_active", True, timeout=60)

        return self._generate_image_via_worker(prompt, style)

    def _generate_image_via_worker(self, prompt: str, style: str = "") -> str:
        from animetix.tasks_client import enqueue_task
        from django.core.cache import cache

        # Increment queue length
        try:
            queue_len = cache.get("self_hosted_image_worker:queue_length", 0)
            cache.set("self_hosted_image_worker:queue_length", queue_len + 1)
        except Exception as e:
            logger.debug(f"Could not increment worker queue length: {e}")

        try:
            logger.info("Enqueuing image generation task to self-hosted worker queue.")
            task_id = enqueue_task(
                "self_hosted_image_generation_task", prompt=prompt, style=style
            )

            # Synchronously poll the cache for task completion (up to 30s)
            start_time = time.time()
            timeout = 30.0
            poll_interval = 0.2

            while time.time() - start_time < timeout:
                task_data = cache.get(f"task_result:{task_id}")
                if task_data and isinstance(task_data, dict):
                    if task_data.get("ready") or task_data.get("state") in [
                        "SUCCESS",
                        "FAILURE",
                    ]:
                        state = task_data.get("state") or task_data.get("status")
                        if state in ["SUCCESS", "success"]:
                            result = task_data.get("result")
                            if isinstance(result, dict) and "error" in result:
                                raise Exception(result["error"])
                            return str(result) if result else ""
                        else:
                            error_info = (
                                task_data.get("result", {}).get("error")
                                if isinstance(task_data.get("result"), dict)
                                else task_data.get("error", "Unknown error")
                            )
                            raise Exception(f"Worker task failed: {error_info}")
                time.sleep(poll_interval)

            raise TimeoutError(
                "Timeout waiting for self-hosted image generation worker task."
            )
        except Exception as e:
            logger.error(f"Failed to generate image via self-hosted worker: {e}")
            # Decrement queue length on failure (since the finally block of the task might not run if it never started)
            try:
                queue_len = cache.get("self_hosted_image_worker:queue_length", 0)
                cache.set(
                    "self_hosted_image_worker:queue_length", max(0, queue_len - 1)
                )
                if max(0, queue_len - 1) <= 0:
                    cache.set("self_hosted_image_worker:status", "idle")
            except Exception as cache_err:
                logger.debug(f"Could not decrement worker queue length: {cache_err}")
            raise e

    def _fallback_call(self, method_name: str, *args, **kwargs):
        capable_adapters = self._capabilities.for_method(method_name)
        if not capable_adapters:
            capable_adapters = self.adapters

        ordered_adapters = self._get_ordered_adapters(capable_adapters)
        last_error = ""  # Initialize last_error
        for adapter in ordered_adapters:
            if not hasattr(adapter, method_name) or not callable(
                getattr(adapter, method_name)
            ):
                continue
            start_time = time.time()
            try:
                method = getattr(adapter, method_name)
                res = method(*args, **kwargs)
                latency = time.time() - start_time

                if res is not None:
                    logger.info(
                        f"✅ [Fallback] {adapter.__class__.__name__}.{method_name} success in {latency:.2f}s"
                    )
                    if last_error:
                        # If there was a previous error, log a warning about fallback
                        logger.warning(
                            f"⚠️ [Fallback] Successfully fell back to {adapter.__class__.__name__} for {method_name} after previous failures. Last failure reason: {last_error}"
                        )
                    return res

                self._report_failure(adapter, method_name, "Résultat None", latency)
                last_error = "Résultat None"  # Update last_error for subsequent checks
            except (InferenceNotImplementedError, NotImplementedError) as e:
                logger.debug(
                    f"⚙️ [Fallback] {adapter.__class__.__name__}.{method_name} raised "
                    f"InferenceNotImplementedError/NotImplementedError (not implemented): {e}"
                )
                last_error = str(e)  # Update last_error
                continue
            except Exception as e:
                latency = time.time() - start_time
                self._report_failure(adapter, method_name, f"CRASH: {str(e)}", latency)
                last_error = str(e)  # Update last_error
                continue
        return None

    # --- Implementations déléguées ---
    def calculate_visual_similarity(
        self, query: str, item_id: str, media_type: str
    ) -> float:
        res = self._fallback_call(
            "calculate_visual_similarity", query, item_id, media_type
        )
        return float(res) if res is not None else 0.0

    def get_image_embedding(
        self, image_data: bytes, model_id: Optional[str] = None
    ) -> List[float]:
        return self._fallback_call("get_image_embedding", image_data, model_id) or []

    def get_text_embedding(self, text: str) -> List[float]:
        return self._fallback_call("get_text_embedding", text) or []

    def classify_image(
        self,
        image_data: bytes,
        candidate_labels: List[str],
        model_id: Optional[str] = None,
    ) -> Dict[str, float]:
        return (
            self._fallback_call(
                "classify_image", image_data, candidate_labels, model_id
            )
            or {}
        )

    def detect_objects(
        self,
        image_data: bytes,
        candidate_queries: List[str],
        model_id: Optional[str] = None,
    ) -> List[Dict]:
        return (
            self._fallback_call(
                "detect_objects", image_data, candidate_queries, model_id
            )
            or []
        )

    def get_video_temporal_embeddings(self, video_data: bytes) -> List[Dict[str, Any]]:
        return self._fallback_call("get_video_temporal_embeddings", video_data) or []

    def localize_video_actions(
        self, video_data: bytes, action_queries: List[str]
    ) -> List[Dict[str, Any]]:
        return (
            self._fallback_call("localize_video_actions", video_data, action_queries)
            or []
        )

    def transform_image_to_anime(
        self, image_data: bytes, studio_style: str, prompt: str = ""
    ) -> str:
        return (
            self._fallback_call(
                "transform_image_to_anime", image_data, studio_style, prompt
            )
            or ""
        )

    def transform_video_to_anime(
        self, video_data: bytes, studio_style: str, prompt: str = ""
    ) -> str:
        return (
            self._fallback_call(
                "transform_video_to_anime", video_data, studio_style, prompt
            )
            or ""
        )

    def generate_soundscape(
        self, video_metadata: Dict[str, Any], prompt: Optional[str] = None
    ) -> str:
        return self._fallback_call("generate_soundscape", video_metadata, prompt) or ""

    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]:
        return self._fallback_call("process_manga_page", image_data) or {}

    def translate_manga_page(
        self, image_data: bytes, target_lang: str = "Français"
    ) -> Dict[str, Any]:
        return (
            self._fallback_call("translate_manga_page", image_data, target_lang) or {}
        )

    def inpaint_text_bubbles(
        self, image_data: bytes, text_placements: List[Dict]
    ) -> str:
        return (
            self._fallback_call("inpaint_text_bubbles", image_data, text_placements)
            or ""
        )

    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        return self._fallback_call("moderate_content", text, categories) or {
            "is_safe": True
        }

    def generate_image_description(self, image_data: bytes, prompt: str = "") -> str:
        return (
            self._fallback_call("generate_image_description", image_data, prompt) or ""
        )

    def generate_video_description(self, video_data: bytes, prompt: str = "") -> str:
        return (
            self._fallback_call("generate_video_description", video_data, prompt) or ""
        )

    def get_diagnostics(self, prompt: str, completion: str) -> Dict[str, Any]:
        return self._fallback_call("get_diagnostics", prompt, completion) or {}

    def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]:
        if self._last_completion == completion and self._last_logprobs:
            logprobs = [
                lp.logprob for lp in self._last_logprobs if lp.logprob is not None
            ]
            if logprobs:
                import numpy as np  # noqa: E402

                avg_entropy = -sum(logprobs) / len(logprobs)
                confidence = max(0.0, min(1.0, 1.0 - (avg_entropy / 10.8)))
                perplexity = float(np.exp(avg_entropy))
                logger.info(
                    "📊 FallbackInferenceAdapter: Using real logprobs from cache."
                )
                return {
                    "entropy": round(avg_entropy, 4),
                    "perplexity": round(perplexity, 4),
                    "confidence": round(confidence, 4),
                }
        return self._fallback_call("calculate_uncertainty", prompt, completion) or {}

    def clone_voice(
        self, text: str, reference_audio: bytes, language: str = "fr"
    ) -> bytes:
        return (
            self._fallback_call("clone_voice", text, reference_audio, language) or b""
        )

    def speech_to_speech(self, audio_input: bytes, system_prompt: str = "") -> bytes:
        return (
            self._fallback_call("speech_to_speech", audio_input, system_prompt) or b""
        )

    def estimate_depth(self, image_data: bytes) -> bytes:
        return self._fallback_call("estimate_depth", image_data) or b""

    def generate_3d_scene(
        self, image_data: bytes, depth_map: bytes, mode: str = "gaussian_splatting"
    ) -> Dict[str, Any]:
        return (
            self._fallback_call("generate_3d_scene", image_data, depth_map, mode) or {}
        )

    def visual_rerank(
        self, query: str, image_urls: List[str], system_prompt: str = ""
    ) -> List[Dict[str, Any]]:
        return (
            self._fallback_call("visual_rerank", query, image_urls, system_prompt) or []
        )

    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]:
        return self._fallback_call("get_multimodal_late_interaction", image_data) or []

    def health_check(self) -> dict:
        statuses = [a.health_check() for a in self.adapters]
        is_online = any(s.get("status") == "online" for s in statuses)
        return {"status": "online" if is_online else "offline", "adapters": statuses}

    def set_primary_adapter(self, index: int) -> bool:
        """Change dynamiquement l'adaptateur prioritaire."""
        if 0 <= index < len(self.adapters):
            adapter = self.adapters.pop(index)
            self.adapters.insert(0, adapter)
            self._capabilities.rebuild(self.adapters)
            logger.info(
                f"🔄 [Fallback] Primary adapter set to {adapter.__class__.__name__}"
            )
            return True
        return False

    @property
    def primary_adapter(self):
        return self.adapters[0] if self.adapters else None

    def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
        """Ré-ordonne les documents avec repli si nécessaire."""
        if not documents:
            return []

        last_error = ""
        ordered_adapters = self._get_ordered_adapters(self.adapters)
        for adapter in ordered_adapters:
            if not hasattr(adapter, "rerank_documents") or not callable(
                getattr(adapter, "rerank_documents")
            ):
                continue

            adapter_name = adapter.__class__.__name__
            start_time = time.time()
            try:
                logger.info(f"🔄 [Fallback] Trying {adapter_name}.rerank_documents...")
                scores = adapter.rerank_documents(query, documents)
                latency = time.time() - start_time

                if scores and len(scores) == len(documents):
                    logger.info(
                        f"✅ [Fallback] {adapter_name}.rerank_documents success in {latency:.2f}s!"
                    )
                    return scores

                last_error = "Résultat vide ou taille incorrecte"
                self._report_failure(adapter, "rerank_documents", last_error, latency)
            except Exception as e:
                latency = time.time() - start_time
                last_error = str(e)
                self._report_failure(
                    adapter, "rerank_documents", f"CRASH: {last_error}", latency
                )
                continue

        logger.warning(
            f"⚠️ All rerankers failed. Falling back to default scoring (0.0). Last error: {last_error}"
        )
        return [0.0] * len(documents)

    def generate_structured(
        self,
        prompt: str,
        response_model: type,
        system_prompt: str = "Tu es un expert en extraction de données structurées.",
        max_retries: int = 3,
    ) -> Any:
        """Génération structurée avec repli."""
        last_error = ""
        ordered_adapters = self._get_ordered_adapters(self.adapters)
        for adapter in ordered_adapters:
            start_time = time.time()
            try:
                # Vérifier si l'adaptateur supporte la génération structurée
                if not hasattr(adapter, "generate_structured"):
                    continue

                logger.info(
                    f"🔄 [Fallback Structured] Trying {adapter.__class__.__name__}..."
                )
                result = adapter.generate_structured(
                    prompt, response_model, system_prompt, max_retries
                )
                latency = time.time() - start_time

                if result is not None:
                    logger.info(
                        f"✅ [Fallback Structured] {adapter.__class__.__name__} success in {latency:.2f}s"
                    )
                    return result

                self._report_failure(
                    adapter, "generate_structured", "Résultat None", latency, prompt
                )
            except Exception as e:
                latency = time.time() - start_time
                last_error = str(e)
                self._report_failure(
                    adapter,
                    "generate_structured",
                    f"CRASH: {last_error}",
                    latency,
                    prompt,
                )
                continue

        raise Exception(
            f"Échec critique : Tous les adaptateurs ont échoué pour la génération structurée. Dernière erreur: {last_error}"
        )
