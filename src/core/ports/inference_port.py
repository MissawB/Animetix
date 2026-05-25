from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class InferenceNotImplementedError(NotImplementedError):
    """Exception levée lorsqu'une fonctionnalité d'inférence n'est pas supportée par un adaptateur."""
    pass

class InferencePort(ABC):
    def generate(
        self, 
        prompt: str, 
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False
    ) -> str:
        """Génère du texte à partir d'un prompt. thinking_budget > 0 ou thinking_mode=True active le raisonnement approfondi."""
        raise InferenceNotImplementedError("generate not implemented for this adapter")

    def stream_generate(
        self, 
        prompt: str, 
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False
    ):
        """Génère du texte en flux (streaming) à partir d'un prompt. thinking_budget > 0 ou thinking_mode=True active le raisonnement approfondi."""
        raise InferenceNotImplementedError("stream_generate not implemented for this adapter")

    def generate_structured(
        self, 
        prompt: str, 
        response_model: type,
        system_prompt: str = "Tu es un expert en extraction de données structurées.",
        max_retries: int = 3
    ) -> Any:
        """Génère une réponse structurée validée par un modèle Pydantic. Implémentation par défaut via texte pur + JSON parsing."""
        import json
        import re
        for i in range(max_retries):
            try:
                # Ajoute une instruction de formatage au système si ce n'est pas déjà fait
                format_instruction = "\nRéponds UNIQUEMENT avec un objet JSON valide."
                response = self.generate(prompt, system_prompt + format_instruction)
                match = re.search(r'\{.*\}', response, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    if hasattr(response_model, "model_validate"):
                        return response_model.model_validate(data)
                    return data
            except Exception as e:
                if i == max_retries - 1:
                    raise e
        raise InferenceNotImplementedError("generate_structured failed to produce valid JSON")

    def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
        """Évalue la pertinence de plusieurs documents par rapport à une requête (Cross-Encoder)."""
        raise InferenceNotImplementedError("rerank_documents not implemented for this adapter")

    def generate_image(self, prompt: str, style: str = "") -> str:
        """Génère une image à partir d'un prompt et retourne une URL ou Base64."""
        raise InferenceNotImplementedError("generate_image not implemented for this adapter")

    def calculate_visual_similarity(self, query: str, item_id: str, media_type: str) -> float:
        """Calcule la similarité entre un texte et une image d'un item."""
        raise InferenceNotImplementedError("calculate_visual_similarity not implemented for this adapter")

    def get_image_embedding(self, image_data: bytes, model_id: Optional[str] = None) -> List[float]:
        """Génère un embedding vectoriel à partir d'une image."""
        raise InferenceNotImplementedError("get_image_embedding not implemented for this adapter")

    def classify_image(self, image_data: bytes, candidate_labels: List[str], model_id: Optional[str] = None) -> Dict[str, float]:
        """Réalise une classification zero-shot d'une image."""
        raise InferenceNotImplementedError("classify_image not implemented for this adapter")

    def detect_objects(self, image_data: bytes, candidate_queries: List[str], model_id: Optional[str] = None) -> List[Dict]:
        """Détecte des objets ou attributs dans une image (Open-World Detection)."""
        raise InferenceNotImplementedError("detect_objects not implemented for this adapter")

    # --- New Methods for Creative Modes ---

    def get_video_temporal_embeddings(self, video_data: bytes) -> List[Dict[str, Any]]:
        """Génère des embeddings pour chaque segment d'une vidéo (Video-RAG)."""
        raise InferenceNotImplementedError("get_video_temporal_embeddings not implemented for this adapter")

    def localize_video_actions(self, video_data: bytes, action_queries: List[str]) -> List[Dict[str, Any]]:
        """Détecte dynamiquement le début et la fin d'actions spécifiques (TAL - Temporal Action Localization)."""
        raise InferenceNotImplementedError("localize_video_actions not implemented for this adapter")

    def transform_image_to_anime(self, image_data: bytes, studio_style: str, prompt: str = "") -> str:
        """Transforme une image réelle en anime via Diffusion + IP-Adapter."""
        raise InferenceNotImplementedError("transform_image_to_anime not implemented for this adapter")

    def transform_video_to_anime(self, video_data: bytes, studio_style: str, prompt: str = "") -> str:
        """Applique un Neural Style Transfer SOTA (type FateZero) sur une vidéo avec consistance par attention."""
        raise InferenceNotImplementedError("transform_video_to_anime not implemented for this adapter")

    def generate_soundscape(self, video_metadata: Dict[str, Any], prompt: Optional[str] = None) -> str:
        """Génère une ambiance sonore ou une musique (type AudioLDM) basée sur le contenu d'une vidéo."""
        raise InferenceNotImplementedError("generate_soundscape not implemented for this adapter")

    def clone_voice(self, text: str, reference_audio: bytes, language: str = "fr") -> bytes:
        """Utilise le Zero-Shot Voice Cloning (RVC) pour synthétiser du texte avec la voix de référence."""
        raise InferenceNotImplementedError("clone_voice not implemented for this adapter")

    def speech_to_speech(self, audio_input: bytes, system_prompt: str = "") -> bytes:
        """Passe par un LLM natif multimodal (ex: Qwen2-Audio) pour une interaction End-to-End Voice sans latence TTS."""
        raise InferenceNotImplementedError("speech_to_speech not implemented for this adapter")

    def estimate_depth(self, image_data: bytes) -> bytes:
        """Estime la carte de profondeur (Depth Map) d'une image 2D (type DepthAnything)."""
        raise InferenceNotImplementedError("estimate_depth not implemented for this adapter")

    def generate_3d_scene(self, image_data: bytes, depth_map: bytes) -> Dict[str, Any]:
        """Génère un espace 3D navigable (Gaussian Splatting / NeRF) à partir d'une image et de sa profondeur, avec in-painting 3D."""
        raise InferenceNotImplementedError("generate_3d_scene not implemented for this adapter")

    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]:
        """Segmente les cases et extrait le texte d'une planche de manga (OCR)."""
        raise InferenceNotImplementedError("process_manga_page not implemented for this adapter")

    def translate_manga_page(self, image_data: bytes, target_lang: str = "Français") -> Dict[str, Any]:
        """Détecte, OCR, traduit et redessine le texte dans les bulles d'une page de manga."""
        raise InferenceNotImplementedError("translate_manga_page not implemented for this adapter")

    def inpaint_text_bubbles(self, image_data: bytes, text_placements: List[Dict]) -> str:
        """Réincruste du texte traduit dans les bulles d'une image (In-painting)."""
        raise InferenceNotImplementedError("inpaint_text_bubbles not implemented for this adapter")

    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """Analyse le texte pour détecter du contenu inapproprié ou des spoilers (Guardrail)."""
        raise InferenceNotImplementedError("moderate_content not implemented for this adapter")

    def generate_image_description(self, image_data: bytes, prompt: str = "Décris cette image d'anime de manière très détaillée.") -> str:
        """Utilise un VLM (Visual Language Model) pour générer une description narrative d'une image."""
        raise InferenceNotImplementedError("generate_image_description not implemented for this adapter")

    def get_diagnostics(self, prompt: str, completion: str) -> Dict[str, Any]:
        """Récupère les données d'activation internes (Logit Lens, Attention) pour l'interprétabilité."""
        raise InferenceNotImplementedError("get_diagnostics not implemented for this adapter")

    def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]:
        """Calcule la certitude mathématique (entropie, perplexité) d'une génération."""
        raise InferenceNotImplementedError("calculate_uncertainty not implemented for this adapter")

    @abstractmethod
    def health_check(self) -> dict:
        """Vérifie l'état de l'unité de calcul."""
        pass

    def visual_rerank(
        self, 
        query: str, 
        image_urls: List[str], 
        system_prompt: str = "Tu es un expert en analyse visuelle d'anime."
    ) -> List[Dict[str, Any]]:
        """Utilise un VLM pour classer une liste d'images par pertinence visuelle."""
        raise InferenceNotImplementedError("visual_rerank not implemented for this adapter")

    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]:
        """Génère des embeddings multi-vecteurs (type ColBERT/ColEmbed) pour une image."""
        raise InferenceNotImplementedError("get_multimodal_late_interaction not implemented for this adapter")
