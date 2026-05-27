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
        # TODO: implement generate method for this adapter
        pass

    def stream_generate(
        self, 
        prompt: str, 
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False
    ):
        """Génère du texte en flux (streaming) à partir d'un prompt. thinking_budget > 0 ou thinking_mode=True active le raisonnement approfondi."""
        # TODO: implement stream_generate method for this adapter
        pass

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
        # TODO: implement rerank_documents method for this adapter
        pass

    def generate_image(self, prompt: str, style: str = "") -> str:
        """Génère une image à partir d'un prompt et retourne une URL ou Base64."""
        # TODO: implement generate_image method for this adapter
        pass

    def generate_sprite(self, prompt: str, style: str = "") -> str:
        """Génère un sprite de personnage (généralement sur fond transparent ou blanc)."""
        return self.generate_image(f"{prompt}, full body portrait on pure white background, anime character sheet style", style)

    def calculate_visual_similarity(self, query: str, item_id: str, media_type: str) -> float:
        """Calcule la similarité entre un texte et une image d'un item."""
        # TODO: implement calculate_visual_similarity method for this adapter
        pass

    def get_image_embedding(self, image_data: bytes, model_id: Optional[str] = None) -> List[float]:
        """Génère un embedding vectoriel à partir d'une image."""
        # TODO: implement get_image_embedding method for this adapter
        pass

    def classify_image(self, image_data: bytes, candidate_labels: List[str], model_id: Optional[str] = None) -> Dict[str, float]:
        """Réalise une classification zero-shot d'une image."""
        # TODO: implement classify_image method for this adapter
        pass

    def detect_objects(self, image_data: bytes, candidate_queries: List[str], model_id: Optional[str] = None) -> List[Dict]:
        """Détecte des objets ou attributs dans une image (Open-World Detection)."""
        # TODO: implement detect_objects method for this adapter
        pass

    # --- New Methods for Creative Modes ---

    def get_video_temporal_embeddings(self, video_data: bytes) -> List[Dict[str, Any]]:
        """Génère des embeddings pour chaque segment d'une vidéo (Video-RAG)."""
        # TODO: implement get_video_temporal_embeddings method for this adapter
        pass

    def localize_video_actions(self, video_data: bytes, action_queries: List[str]) -> List[Dict[str, Any]]:
        """Détecte dynamiquement le début et la fin d'actions spécifiques (TAL - Temporal Action Localization)."""
        # TODO: implement localize_video_actions method for this adapter
        pass

    def transform_image_to_anime(self, image_data: bytes, studio_style: str, prompt: str = "") -> str:
        """Transforme une image réelle en anime via Diffusion + IP-Adapter."""
        # TODO: implement transform_image_to_anime method for this adapter
        pass

    def transform_video_to_anime(self, video_data: bytes, studio_style: str, prompt: str = "") -> str:
        """Applique un Neural Style Transfer SOTA (type FateZero) sur une vidéo avec consistance par attention."""
        # TODO: implement transform_video_to_anime method for this adapter
        pass

    def generate_soundscape(self, video_metadata: Dict[str, Any], prompt: Optional[str] = None) -> str:
        """Génère une ambiance sonore ou une musique (type AudioLDM) basée sur le contenu d'une vidéo."""
        # TODO: implement generate_soundscape method for this adapter
        pass

    def clone_voice(self, text: str, reference_audio: bytes, language: str = "fr") -> bytes:
        """Utilise le Zero-Shot Voice Cloning (RVC) pour synthétiser du texte avec la voix de référence."""
        # TODO: implement clone_voice method for this adapter
        pass

    def speech_to_speech(self, audio_input: bytes, system_prompt: str = "") -> bytes:
        """Passe par un LLM natif multimodal (ex: Qwen2-Audio) pour une interaction End-to-End Voice sans latence TTS."""
        # TODO: implement speech_to_speech method for this adapter
        pass

    def estimate_depth(self, image_data: bytes) -> bytes:
        """Estime la carte de profondeur (Depth Map) d'une image 2D (type DepthAnything)."""
        # TODO: implement estimate_depth method for this adapter
        pass

    def generate_3d_scene(self, image_data: bytes, depth_map: bytes) -> Dict[str, Any]:
        """Génère un espace 3D navigable (Gaussian Splatting / NeRF) à partir d'une image et de sa profondeur, avec in-painting 3D."""
        # TODO: implement generate_3d_scene method for this adapter
        pass

    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]:
        """Segmente les cases et extrait le texte d'une planche de manga (OCR)."""
        # TODO: implement process_manga_page method for this adapter
        pass

    def translate_manga_page(self, image_data: bytes, target_lang: str = "Français") -> Dict[str, Any]:
        """Détecte, OCR, traduit et redessine le texte dans les bulles d'une page de manga."""
        # TODO: implement translate_manga_page method for this adapter
        pass

    def inpaint_text_bubbles(self, image_data: bytes, text_placements: List[Dict]) -> str:
        """Réincruste du texte traduit dans les bulles d'une image (In-painting)."""
        # TODO: implement inpaint_text_bubbles method for this adapter
        pass

    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """Analyse le texte pour détecter du contenu inapproprié ou des spoilers (Guardrail)."""
        # TODO: implement moderate_content method for this adapter
        pass

    def generate_image_description(self, image_data: bytes, prompt: str = "Décris cette image d'anime de manière très détaillée.") -> str:
        """Utilise un VLM (Visual Language Model) pour générer une description narrative d'une image."""
        # TODO: implement generate_image_description method for this adapter
        pass

    def get_diagnostics(self, prompt: str, completion: str) -> Dict[str, Any]:
        """Récupère les données d'activation internes (Logit Lens, Attention) pour l'interprétabilité."""
        # TODO: implement get_diagnostics method for this adapter
        pass

    def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]:
        """Calcule la certitude mathématique (entropie, perplexité) d'une génération."""
        # TODO: implement calculate_uncertainty method for this adapter
        pass

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
        # TODO: implement visual_rerank method for this adapter
        pass

    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]:
        """Génère des embeddings multi-vecteurs (type ColBERT/ColEmbed) pour une image."""
        # TODO: implement get_multimodal_late_interaction method for this adapter
        pass
