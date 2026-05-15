from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class InferencePort(ABC):
    @abstractmethod
    def generate(
        self, 
        prompt: str, 
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0
    ) -> str:
        """Génère du texte à partir d'un prompt. thinking_budget > 0 active le raisonnement approfondi."""
        pass

    @abstractmethod
    def stream_generate(
        self, 
        prompt: str, 
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0
    ):
        """Génère du texte en flux (streaming) à partir d'un prompt. thinking_budget > 0 active le raisonnement approfondi."""
        pass

    @abstractmethod
    def calculate_visual_similarity(self, query: str, item_id: str, media_type: str) -> float:
        """Calcule la similarité entre un texte et une image d'un item."""
        pass

    @abstractmethod
    def get_image_embedding(self, image_data: bytes, model_id: Optional[str] = None) -> List[float]:
        """Génère un embedding vectoriel à partir d'une image."""
        pass

    @abstractmethod
    def classify_image(self, image_data: bytes, candidate_labels: List[str], model_id: Optional[str] = None) -> Dict[str, float]:
        """Réalise une classification zero-shot d'une image."""
        pass

    @abstractmethod
    def detect_objects(self, image_data: bytes, candidate_queries: List[str], model_id: Optional[str] = None) -> List[Dict]:
        """Détecte des objets ou attributs dans une image (Open-World Detection)."""
        pass

    # --- New Methods for Creative Modes ---

    @abstractmethod
    def get_video_temporal_embeddings(self, video_data: bytes) -> List[Dict[str, Any]]:
        """Génère des embeddings pour chaque segment d'une vidéo (Video-RAG)."""
        pass

    @abstractmethod
    def localize_video_actions(self, video_data: bytes, action_queries: List[str]) -> List[Dict[str, Any]]:
        """Détecte dynamiquement le début et la fin d'actions spécifiques (TAL - Temporal Action Localization)."""
        pass

    @abstractmethod
    def transform_image_to_anime(self, image_data: bytes, studio_style: str, prompt: str = "") -> str:
        """Transforme une image réelle en anime via Diffusion + IP-Adapter."""
        pass

    @abstractmethod
    def transform_video_to_anime(self, video_data: bytes, studio_style: str, prompt: str = "") -> str:
        """Applique un Neural Style Transfer SOTA (type FateZero) sur une vidéo avec consistance par attention."""
        pass

    @abstractmethod
    def generate_soundscape(self, video_metadata: Dict[str, Any], prompt: Optional[str] = None) -> str:
        """Génère une ambiance sonore ou une musique (type AudioLDM) basée sur le contenu d'une vidéo."""
        pass

    @abstractmethod
    def clone_voice(self, text: str, reference_audio: bytes, language: str = "fr") -> bytes:
        """Utilise le Zero-Shot Voice Cloning (RVC) pour synthétiser du texte avec la voix de référence."""
        pass

    @abstractmethod
    def speech_to_speech(self, audio_input: bytes, system_prompt: str = "") -> bytes:
        """Passe par un LLM natif multimodal (ex: Qwen2-Audio) pour une interaction End-to-End Voice sans latence TTS."""
        pass

    @abstractmethod
    def estimate_depth(self, image_data: bytes) -> bytes:
        """Estime la carte de profondeur (Depth Map) d'une image 2D (type DepthAnything)."""
        pass

    @abstractmethod
    def generate_3d_scene(self, image_data: bytes, depth_map: bytes) -> Dict[str, Any]:
        """Génère un espace 3D navigable (Gaussian Splatting / NeRF) à partir d'une image et de sa profondeur, avec in-painting 3D."""
        pass

    @abstractmethod
    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]:
        """Segmente les cases et extrait le texte d'une planche de manga (OCR)."""
        pass

    @abstractmethod
    def inpaint_text_bubbles(self, image_data: bytes, text_placements: List[Dict]) -> str:
        """Réincruste du texte traduit dans les bulles d'une image (In-painting)."""
        pass

    @abstractmethod
    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """Analyse le texte pour détecter du contenu inapproprié ou des spoilers (Guardrail)."""
        pass

    @abstractmethod
    def generate_image_description(self, image_data: bytes, prompt: str = "Décris cette image d'anime de manière très détaillée.") -> str:
        """Utilise un VLM (Visual Language Model) pour générer une description narrative d'une image."""
        pass

    @abstractmethod
    def get_diagnostics(self, prompt: str, completion: str) -> Dict[str, Any]:
        """Récupère les données d'activation internes (Logit Lens, Attention) pour l'interprétabilité."""
        pass

    @abstractmethod
    def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]:
        """Calcule la certitude mathématique (entropie, perplexité) d'une génération."""
        pass

    @abstractmethod
    def health_check(self) -> dict:
        """Vérifie l'état de l'unité de calcul."""
        pass

    @abstractmethod
    def visual_rerank(
        self, 
        query: str, 
        image_urls: List[str], 
        system_prompt: str = "Tu es un expert en analyse visuelle d'anime."
    ) -> List[Dict[str, Any]]:
        """Utilise un VLM pour classer une liste d'images par pertinence visuelle."""
        pass

    @abstractmethod
    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]:
        """Génère des embeddings multi-vecteurs (type ColBERT/ColEmbed) pour une image."""
        pass
