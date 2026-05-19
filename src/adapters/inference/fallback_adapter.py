import logging
import time
from typing import List, Optional, Dict, Any
from core.ports.inference_port import InferencePort

logger = logging.getLogger('animetix.inference.fallback')

class FallbackInferenceAdapter(InferencePort):
    """
    Orchestre une liste d'adaptateurs d'inférence.
    Passe au suivant si l'un d'eux échoue ou retourne une chaîne commençant par 'Erreur'.
    Inclut un mécanisme de monitoring via ObservabilityService.
    """
    def __init__(self, adapters: List[InferencePort], obs_service: Optional[Any] = None):
        self.adapters = [a for a in adapters if a is not None]
        self.obs_service = obs_service

    def _report_failure(self, adapter: InferencePort, method: str, error: str, latency: float, prompt_hint: str = ""):
        """Helper centralisé pour le logging et le monitoring des échecs."""
        adapter_name = adapter.__class__.__name__
        error_msg = f"❌ [Fallback] {adapter_name}.{method} failed after {latency:.2f}s: {error}"
        if prompt_hint:
            error_msg += f" | Prompt hint: {prompt_hint[:50]}..."
        
        logger.error(error_msg)
        
        if self.obs_service:
            self.obs_service.log_error(
                error_type="InferenceAdapterFailure",
                message=f"{adapter_name}.{method}: {error}"
            )
            # On log aussi les métriques d'échec
            self.obs_service.log_inference(
                model_id=adapter_name,
                latency=latency,
                tokens=0,
                metadata={"status": "failed", "method": method, "error": error[:100]}
            )

    def generate(self, prompt: str, system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.", thinking_budget: int = 0, thinking_mode: bool = False) -> str:
        last_error = ""
        for adapter in self.adapters:
            adapter_name = adapter.__class__.__name__
            start_time = time.time()
            try:
                logger.info(f"🔄 [Fallback] Trying {adapter_name}...")
                result = adapter.generate(prompt, system_prompt, thinking_budget, thinking_mode)
                latency = time.time() - start_time
                
                # CRITIQUE : Si le résultat est nul ou commence par "Erreur", on considère ça comme un échec
                if not result or str(result).strip().startswith("Erreur"):
                    last_error = str(result) if result else "Résultat vide"
                    self._report_failure(adapter, "generate", last_error, latency, prompt)
                    continue # On passe au suivant
                
                # Si on est ici, on a un succès !
                logger.info(f"✅ [Fallback] {adapter_name} success in {latency:.2f}s!")
                if self.obs_service:
                    self.obs_service.log_inference(model_id=adapter_name, latency=latency, tokens=len(result)//4)
                return result
                
            except Exception as e:
                latency = time.time() - start_time
                last_error = str(e)
                self._report_failure(adapter, "generate", f"CRASH: {last_error}", latency, prompt)
                continue
                
        return f"Échec critique : Tous les moteurs LLM ont échoué. Dernière erreur: {last_error}"

    def stream_generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False):
        """Streaming avec repli intelligent."""
        for adapter in self.adapters:
            start_time = time.time()
            try:
                # Tentative de premier token pour valider l'adaptateur
                gen = adapter.stream_generate(prompt, system_prompt, thinking_budget, thinking_mode)
                first_chunk = next(gen)
                latency = time.time() - start_time
                
                # Validation du premier chunk
                if first_chunk and not str(first_chunk).strip().startswith("Erreur"):
                    def success_gen():
                        yield first_chunk
                        yield from gen
                    logger.info(f"✅ [Stream Fallback] {adapter.__class__.__name__} success in {latency:.2f}s")
                    return success_gen()
                
                error_hint = str(first_chunk) if first_chunk else "Premier chunk vide"
                self._report_failure(adapter, "stream_generate", error_hint, latency, prompt)
            except StopIteration:
                self._report_failure(adapter, "stream_generate", "StopIteration (Pas de réponse)", time.time() - start_time, prompt)
                continue
            except Exception as e:
                self._report_failure(adapter, "stream_generate", f"CRASH: {str(e)}", time.time() - start_time, prompt)
                continue
        
        # Fallback final vers generate standard (qui a sa propre logique de repli)
        def error_gen(): yield self.generate(prompt, system_prompt, thinking_budget, thinking_mode)
        return error_gen()

    def generate_image(self, prompt: str, style: str = "") -> str:
        """Génère une image avec repli."""
        return self._fallback_call("generate_image", prompt, style) or ""

    def _fallback_call(self, method_name: str, *args, **kwargs):
        for adapter in self.adapters:
            start_time = time.time()
            try:
                method = getattr(adapter, method_name)
                res = method(*args, **kwargs)
                latency = time.time() - start_time
                
                # Si c'est une liste ou dict vide, on considère ça comme un échec potentiel selon le contexte,
                # mais ici on reste simple.
                if res is not None: 
                    logger.info(f"✅ [Fallback] {adapter.__class__.__name__}.{method_name} success in {latency:.2f}s")
                    return res
                
                self._report_failure(adapter, method_name, "Résultat None", latency)
            except Exception as e:
                latency = time.time() - start_time
                self._report_failure(adapter, method_name, f"CRASH: {str(e)}", latency)
                continue
        return None

    # --- Implementations déléguées ---
    def calculate_visual_similarity(self, query: str, item_id: str, media_type: str) -> float:
        res = self._fallback_call("calculate_visual_similarity", query, item_id, media_type)
        return float(res) if res is not None else 0.0

    def get_image_embedding(self, image_data: bytes, model_id: Optional[str] = None) -> List[float]:
        return self._fallback_call("get_image_embedding", image_data, model_id) or []

    def get_text_embedding(self, text: str) -> List[float]:
        return self._fallback_call("get_text_embedding", text) or []

    def classify_image(self, image_data: bytes, candidate_labels: List[str], model_id: Optional[str] = None) -> Dict[str, float]:
        return self._fallback_call("classify_image", image_data, candidate_labels, model_id) or {}

    def detect_objects(self, image_data: bytes, candidate_queries: List[str], model_id: Optional[str] = None) -> List[Dict]:
        return self._fallback_call("detect_objects", image_data, candidate_queries, model_id) or []

    def get_video_temporal_embeddings(self, video_data: bytes) -> List[Dict[str, Any]]:
        return self._fallback_call("get_video_temporal_embeddings", video_data) or []

    def localize_video_actions(self, video_data: bytes, action_queries: List[str]) -> List[Dict[str, Any]]:
        return self._fallback_call("localize_video_actions", video_data, action_queries) or []

    def transform_image_to_anime(self, image_data: bytes, studio_style: str, prompt: str = "") -> str:
        return self._fallback_call("transform_image_to_anime", image_data, studio_style, prompt) or ""

    def transform_video_to_anime(self, video_data: bytes, studio_style: str, prompt: str = "") -> str:
        return self._fallback_call("transform_video_to_anime", video_data, studio_style, prompt) or ""

    def generate_soundscape(self, video_metadata: Dict[str, Any], prompt: Optional[str] = None) -> str:
        return self._fallback_call("generate_soundscape", video_metadata, prompt) or ""

    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]:
        return self._fallback_call("process_manga_page", image_data) or {}

    def translate_manga_page(self, image_data: bytes, target_lang: str = "Français") -> Dict[str, Any]:
        return self._fallback_call("translate_manga_page", image_data, target_lang) or {}

    def inpaint_text_bubbles(self, image_data: bytes, text_placements: List[Dict]) -> str:
        return self._fallback_call("inpaint_text_bubbles", image_data, text_placements) or ""

    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        return self._fallback_call("moderate_content", text, categories) or {"is_safe": True}

    def generate_image_description(self, image_data: bytes, prompt: str = "") -> str:
        return self._fallback_call("generate_image_description", image_data, prompt) or ""

    def get_diagnostics(self, prompt: str, completion: str) -> Dict[str, Any]:
        return self._fallback_call("get_diagnostics", prompt, completion) or {}

    def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]:
        return self._fallback_call("calculate_uncertainty", prompt, completion) or {}

    def clone_voice(self, text: str, reference_audio: bytes, language: str = "fr") -> bytes:
        return self._fallback_call("clone_voice", text, reference_audio, language) or b""

    def speech_to_speech(self, audio_input: bytes, system_prompt: str = "") -> bytes:
        return self._fallback_call("speech_to_speech", audio_input, system_prompt) or b""

    def estimate_depth(self, image_data: bytes) -> bytes:
        return self._fallback_call("estimate_depth", image_data) or b""

    def generate_3d_scene(self, image_data: bytes, depth_map: bytes) -> Dict[str, Any]:
        return self._fallback_call("generate_3d_scene", image_data, depth_map) or {}

    def visual_rerank(self, query: str, image_urls: List[str], system_prompt: str = "") -> List[Dict[str, Any]]:
        return self._fallback_call("visual_rerank", query, image_urls, system_prompt) or []

    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]:
        return self._fallback_call("get_multimodal_late_interaction", image_data) or []

    def health_check(self) -> dict:
        statuses = [a.health_check() for a in self.adapters]
        is_online = any(s.get("status") == "online" for s in statuses)
        return {"status": "online" if is_online else "offline", "adapters": statuses}
