import asyncio
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional

from ..domain.entities.ai_schemas import InferenceResponse
from .usage_port import UsagePort


class InferenceNotImplementedError(NotImplementedError):
    """Exception levée lorsqu'une fonctionnalité d'inférence n'est pas supportée par un adaptateur."""

    pass


# Provenance d'un verdict de modération, sous la clé "source". Les trois valeurs
# ont la MÊME forme de dict mais pas la même valeur de preuve, et seule la
# première est une décision :
#   - MODERATION_SOURCE_MODEL : un modèle a lu le texte et tranché ;
#   - MODERATION_SOURCE_KEYWORDS : l'appel modèle a échoué, il ne reste qu'une
#     liste de gros mots (accompagné de "degraded": True) ;
#   - aucune clé : un remplissage (`{"is_safe": True}`) ou un adaptateur d'une
#     version antérieure — donc une preuve manquante, pas une bonne nouvelle.
# `GuardrailService._is_model_verdict` s'en sert pour décider s'il peut faire
# l'économie de la modération fine par prompt, ou si le contrôle reste à faire.
MODERATION_SOURCE_MODEL = "model"
MODERATION_SOURCE_KEYWORDS = "keyword-fallback"


class BaseInferencePort(ABC):
    """Port de base pour la gestion de l'usage et des métriques d'inférence."""

    def __init__(self, usage_port: Optional[UsagePort] = None):
        self.usage_port = usage_port

    def _log_usage(
        self,
        engine: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        units: int = 0,
        allocated_budget: int = 0,
    ):
        if self.usage_port:
            self.usage_port.log_usage(
                engine,
                input_tokens,
                output_tokens,
                units,
                allocated_budget=allocated_budget,
            )


class TextInferencePort(BaseInferencePort):
    """Port spécialisé pour l'inférence textuelle, les embeddings de texte, le reranking et le guardrail."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs,
    ) -> InferenceResponse:
        """Génère du texte à partir d'un prompt."""
        pass

    async def agenerate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs,
    ) -> InferenceResponse:
        """Variante asynchrone de :meth:`generate`."""
        return await asyncio.to_thread(
            self.generate,
            prompt,
            system_prompt=system_prompt,
            thinking_budget=thinking_budget,
            thinking_mode=thinking_mode,
            include_logprobs=include_logprobs,
            **kwargs,
        )

    @abstractmethod
    def stream_generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs,
    ):
        """Génère du texte en flux (streaming) à partir d'un prompt."""
        pass

    async def astream_generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs,
    ) -> AsyncGenerator[InferenceResponse, None]:
        """Génère du texte en flux de manière asynchrone."""
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()
        DONE = object()

        def producer():
            try:
                for chunk in self.stream_generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    thinking_budget=thinking_budget,
                    thinking_mode=thinking_mode,
                    include_logprobs=include_logprobs,
                    **kwargs,
                ):
                    loop.call_soon_threadsafe(queue.put_nowait, chunk)
            except Exception as e:
                loop.call_soon_threadsafe(queue.put_nowait, e)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, DONE)

        loop.run_in_executor(None, producer)

        while True:
            item = await queue.get()
            if item is DONE:
                break
            if isinstance(item, Exception):
                raise item
            yield item

    def generate_structured(
        self,
        prompt: str,
        response_model: type,
        system_prompt: str = "Tu es un expert en extraction de données structurées.",
        max_retries: int = 3,
    ) -> Any:
        """Génère une réponse structurée validée par un modèle Pydantic."""
        import json  # noqa: E402
        import re  # noqa: E402

        for i in range(max_retries):
            try:
                format_instruction = "\nRéponds UNIQUEMENT avec un objet JSON valide."
                response = self.generate(prompt, system_prompt + format_instruction)
                response_text = response.text if hasattr(response, "text") else response
                if not isinstance(response_text, str):
                    response_text = str(response_text)
                match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    if hasattr(response_model, "model_validate"):
                        return response_model.model_validate(data)
                    return data
            except Exception as e:
                if i == max_retries - 1:
                    raise e
        raise InferenceNotImplementedError(
            "generate_structured failed to produce valid JSON"
        )

    @abstractmethod
    def get_text_embedding(self, text: str) -> List[float]:
        """Génère un embedding vectoriel pour un texte donné."""
        pass

    def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
        """Évalue la pertinence de plusieurs documents par rapport à une requête (Cross-Encoder)."""
        raise InferenceNotImplementedError(
            "rerank_documents not implemented for this adapter"
        )

    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """Analyse le texte pour détecter du contenu inapproprié ou des spoilers (Guardrail)."""
        categories_str = ", ".join(categories)
        prompt = (
            f"Analyse le texte suivant pour détecter s'il contient du contenu inapproprié "
            f"ou s'il correspond à l'une des catégories suivantes : {categories_str}.\n"
            f'Texte : "{text}"\n'
            f"Réponds UNIQUEMENT sous la forme d'un objet JSON contenant ces clés :\n"
            f'{{"is_safe": bool, "detected_categories": [str], "reason": str}}'
        )
        try:
            res = self.generate_structured(
                prompt=prompt,
                response_model=dict,
                system_prompt="Tu es un agent de modération sémantique expert pour une plateforme Anime/Manga.",
            )
            is_safe = res.get("is_safe", True)
            detected = res.get("detected_categories", [])
            if not isinstance(detected, list):
                detected = []

            return {
                "is_safe": is_safe,
                "detected_categories": detected,
                "action": "block" if not is_safe else "allow",
                "reason": res.get("reason", "Vérification sémantique effectuée."),
                "source": MODERATION_SOURCE_MODEL,
            }
        except Exception as e:
            bad_words = ["hentai", "nsfw", "porn", "sex", "gore", "violence extreme"]
            found = [w for w in bad_words if w in text.lower()]
            is_safe = len(found) == 0
            # Repli par mots-clés : un `is_safe: True` d'ici ne veut dire que
            # « aucun mot de la liste », pas « analysé et jugé sain ». Marqué
            # comme dégradé pour que l'appelant sache qu'il reste un contrôle
            # sémantique à faire.
            return {
                "is_safe": is_safe,
                "detected_categories": found,
                "action": "block" if not is_safe else "allow",
                "reason": f"Vérification par mots-clés effectuée (Échec LLM: {str(e)}).",
                "source": MODERATION_SOURCE_KEYWORDS,
                "degraded": True,
            }

    def get_diagnostics(self, prompt: str, completion: str) -> Dict[str, Any]:
        """Récupère les données d'activation internes (Logit Lens, Attention) pour l'interprétabilité."""
        raise InferenceNotImplementedError(
            "get_diagnostics not implemented for this adapter"
        )

    def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]:
        """Calcule la certitude mathématique (entropie, perplexité) d'une génération."""
        raise InferenceNotImplementedError(
            "calculate_uncertainty not implemented for this adapter"
        )


class VisionInferencePort(BaseInferencePort):
    """Port spécialisé pour l'analyse visuelle, la génération d'images, le Video-RAG et l'OCR manga."""

    def generate_image(self, prompt: str, style: str = "") -> str:
        """Génère une image à partir d'un prompt et retourne une URL ou Base64."""
        raise InferenceNotImplementedError(
            "generate_image not implemented for this adapter"
        )

    def generate_sprite(self, prompt: str, style: str = "") -> str:
        """Génère un sprite de personnage."""
        raise InferenceNotImplementedError(
            "generate_sprite not implemented for this adapter"
        )

    def calculate_visual_similarity(
        self, query: str, item_id: str, media_type: str
    ) -> float:
        """Calcule la similarité entre un texte et une image d'un item."""
        return 0.5

    def get_image_embedding(
        self, image_data: bytes, model_id: Optional[str] = None
    ) -> List[float]:
        """Génère un embedding vectoriel à partir d'une image."""
        raise InferenceNotImplementedError("get_image_embedding not implemented")

    def get_text_embedding_clip(self, text: str, model_id: str) -> List[float]:
        """Tour TEXTE d'un modèle CLIP."""
        raise InferenceNotImplementedError("get_text_embedding_clip not implemented")

    def get_character_embedding(self, image_data: bytes) -> List[float]:
        """Embedding CCIP pour reconnaissance de personnages."""
        raise InferenceNotImplementedError("get_character_embedding not implemented")

    def classify_image(
        self,
        image_data: bytes,
        candidate_labels: List[str],
        model_id: Optional[str] = None,
    ) -> Dict[str, float]:
        """Réalise une classification zero-shot d'une image."""
        raise InferenceNotImplementedError("classify_image not implemented")

    def detect_objects(
        self,
        image_data: bytes,
        candidate_queries: List[str],
        model_id: Optional[str] = None,
    ) -> List[Dict]:
        """Détecte des objets ou attributs dans une image."""
        raise InferenceNotImplementedError("detect_objects not implemented")

    def get_video_temporal_embeddings(self, video_data: bytes) -> List[Dict[str, Any]]:
        """Génère des embeddings pour chaque segment d'une vidéo (Video-RAG)."""
        raise InferenceNotImplementedError(
            "get_video_temporal_embeddings not implemented for this adapter"
        )

    def localize_video_actions(
        self, video_data: bytes, action_queries: List[str]
    ) -> List[Dict[str, Any]]:
        """Détecte dynamiquement le début et la fin d'actions spécifiques dans une vidéo."""
        raise InferenceNotImplementedError("localize_video_actions not implemented")

    def transform_image_to_anime(
        self, image_data: bytes, studio_style: str, prompt: str = ""
    ) -> str:
        """Transforme une image réelle en anime via Diffusion + IP-Adapter."""
        raise InferenceNotImplementedError("transform_image_to_anime not implemented")

    def transform_video_to_anime(
        self, video_data: bytes, studio_style: str, prompt: str = ""
    ) -> str:
        """Applique un Neural Style Transfer sur une vidéo."""
        raise InferenceNotImplementedError(
            "transform_video_to_anime not implemented for this adapter"
        )

    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]:
        """Segmente les cases et extrait le texte d'une planche de manga (OCR)."""
        raise InferenceNotImplementedError(
            "process_manga_page not implemented for this adapter"
        )

    def translate_manga_page(
        self, image_data: bytes, target_lang: str = "Français"
    ) -> Dict[str, Any]:
        """Détecte, OCR, traduit et redessine le texte dans les bulles d'une page de manga."""
        raise InferenceNotImplementedError(
            "translate_manga_page not implemented for this adapter"
        )

    def inpaint_text_bubbles(
        self, image_data: bytes, text_placements: List[Dict]
    ) -> str:
        """Réincruste du texte traduit dans les bulles d'une image (In-painting)."""
        raise InferenceNotImplementedError(
            "inpaint_text_bubbles not implemented for this adapter"
        )

    def generate_image_description(
        self,
        image_data: bytes,
        prompt: str = "Décris cette image d'anime de manière très détaillée.",
    ) -> str:
        """Utilise un VLM pour générer une description narrative d'une image."""
        raise InferenceNotImplementedError(
            "generate_image_description not implemented for this adapter"
        )

    def generate_video_description(
        self,
        video_data: bytes,
        prompt: str = "Décris cette vidéo d'anime de manière très détaillée.",
    ) -> str:
        """Utilise un VLM Vidéo pour générer une description narrative d'une vidéo."""
        raise InferenceNotImplementedError(
            "generate_video_description not implemented for this adapter"
        )

    def visual_rerank(
        self,
        query: str,
        image_urls: List[str],
        system_prompt: str = "Tu es un expert en analyse visuelle d'anime.",
    ) -> List[Dict[str, Any]]:
        """Utilise un VLM pour classer une liste d'images par pertinence visuelle."""
        raise InferenceNotImplementedError(
            "visual_rerank not implemented for this adapter"
        )

    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]:
        """Génère des embeddings multi-vecteurs (type ColBERT/ColEmbed) pour une image."""
        raise InferenceNotImplementedError(
            "get_multimodal_late_interaction not implemented for this adapter"
        )


class AudioInferencePort(BaseInferencePort):
    """Port spécialisé pour la génération audio, la synthèse vocale (TTS) et le Voice Cloning."""

    def generate_soundscape(
        self, video_metadata: Dict[str, Any], prompt: Optional[str] = None
    ) -> str:
        """Génère une ambiance sonore ou une musique basée sur le contenu d'une vidéo."""
        raise InferenceNotImplementedError(
            "generate_soundscape not implemented for this adapter"
        )

    def clone_voice(
        self, text: str, reference_audio: bytes, language: str = "fr"
    ) -> bytes:
        """Utilise le Zero-Shot Voice Cloning (RVC) pour synthétiser du texte avec la voix de référence."""
        raise InferenceNotImplementedError(
            "clone_voice not implemented for this adapter"
        )

    def speech_to_speech(self, audio_input: bytes, system_prompt: str = "") -> bytes:
        """Passe par un LLM natif multimodal pour une interaction End-to-End Voice."""
        raise InferenceNotImplementedError(
            "speech_to_speech not implemented for this adapter"
        )


class Spatial3DInferencePort(BaseInferencePort):
    """Port spécialisé pour la reconstruction 3D, l'estimation de profondeur et le Gaussian Splatting."""

    def estimate_depth(self, image_data: bytes) -> bytes:
        """Estime la carte de profondeur (Depth Map) d'une image 2D."""
        raise InferenceNotImplementedError(
            "estimate_depth not implemented for this adapter"
        )

    def generate_3d_scene(
        self, image_data: bytes, depth_map: bytes, mode: str = "gaussian_splatting"
    ) -> Dict[str, Any]:
        """Génère un espace 3D navigable (Gaussian Splatting / NeRF) à partir d'une image."""
        raise InferenceNotImplementedError(
            "generate_3d_scene not implemented for this adapter"
        )


class InferencePort(
    TextInferencePort,
    VisionInferencePort,
    AudioInferencePort,
    Spatial3DInferencePort,
):
    """
    Port d'inférence combiné (Façade multi-modalités).
    Hérite des 4 ports spécialisés (Text, Vision, Audio, Spatial3D) pour garantir
    une rétro-compatibilité à 100 % avec les adaptateurs et conteneurs existants.
    """

    @abstractmethod
    def health_check(self) -> dict:
        """Vérifie l'état de l'unité de calcul."""
        pass
