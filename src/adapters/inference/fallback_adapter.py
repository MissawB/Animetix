import logging
from typing import List, Optional, Dict, Any
from core.ports.inference_port import InferencePort

logger = logging.getLogger('animetix.inference.fallback')

class FallbackInferenceAdapter(InferencePort):
    """
    Orchestre une liste d'adaptateurs d'inférence.
    Passe au suivant si l'un d'eux échoue ou retourne une chaîne commençant par 'Erreur'.
    """
    def __init__(self, adapters: List[InferencePort]):
        self.adapters = [a for a in adapters if a is not None]

    def generate(self, prompt: str, system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.", thinking_budget: int = 0, thinking_mode: bool = False) -> str:
        last_error = ""
        for adapter in self.adapters:
            adapter_name = adapter.__class__.__name__
            try:
                logger.info(f"🔄 [Fallback] Trying {adapter_name}...")
                result = adapter.generate(prompt, system_prompt, thinking_budget, thinking_mode)
                
                # CRITIQUE : Si le résultat est nul ou commence par "Erreur", on considère ça comme un échec
                if not result or str(result).strip().startswith("Erreur"):
                    last_error = str(result) if result else "Résultat vide"
                    logger.warning(f"⏩ [Fallback] {adapter_name} failed: {last_error[:50]}")
                    continue # On passe au suivant
                
                # Si on est ici, on a un succès !
                logger.info(f"✅ [Fallback] {adapter_name} success!")
                return result
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"❌ [Fallback] {adapter_name} crash: {e}")
                continue
                
        return f"Échec critique : Tous les moteurs LLM ont échoué. Dernière erreur: {last_error}"

    def stream_generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False):
        """Streaming avec repli intelligent."""
        for adapter in self.adapters:
            try:
                # Tentative de premier token pour valider l'adaptateur
                gen = adapter.stream_generate(prompt, system_prompt, thinking_budget, thinking_mode)
                first_chunk = next(gen)
                
                # Validation du premier chunk
                if first_chunk and not str(first_chunk).strip().startswith("Erreur"):
                    def success_gen():
                        yield first_chunk
                        yield from gen
                    return success_gen()
                
                logger.warning(f"⏩ [Stream Fallback] Skipping {adapter.__class__.__name__} due to invalid chunk.")
            except StopIteration:
                continue
            except Exception as e:
                logger.error(f"❌ [Stream Fallback] {adapter.__class__.__name__} failed: {e}")
                continue
        
        # Fallback final vers generate standard (qui a sa propre logique de repli)
        def error_gen(): yield self.generate(prompt, system_prompt, thinking_budget, thinking_mode)
        return error_gen()

    def _fallback_call(self, method_name: str, *args, **kwargs):
        for adapter in self.adapters:
            try:
                method = getattr(adapter, method_name)
                res = method(*args, **kwargs)
                # Si c'est une liste ou dict vide, on considère ça comme un échec potentiel selon le contexte,
                # mais ici on reste simple.
                if res is not None: return res
            except:
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
