from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from .usage_port import UsagePort
from ..domain.entities.ai_schemas import InferenceResponse

class InferenceNotImplementedError(NotImplementedError):
    """Exception levée lorsqu'une fonctionnalité d'inférence n'est pas supportée par un adaptateur."""
    pass

class InferencePort(ABC):
    def __init__(self, usage_port: Optional[UsagePort] = None):
        self.usage_port = usage_port

    def _log_usage(self, engine: str, input_tokens: int = 0, output_tokens: int = 0, units: int = 0):
        if self.usage_port:
            self.usage_port.log_usage(engine, input_tokens, output_tokens, units)

    def generate(
        self, 
        prompt: str, 
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False
    ) -> InferenceResponse:
        """Génère du texte à partir d'un prompt. thinking_budget > 0 ou thinking_mode=True active le raisonnement approfondi."""
        # TODO: implement generate method for this adapter
        raise InferenceNotImplementedError("generate not implemented for this adapter")

    def stream_generate(
        self, 
        prompt: str, 
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False
    ):
        """Génère du texte en flux (streaming) à partir d'un prompt. thinking_budget > 0 ou thinking_mode=True active le raisonnement approfondi."""
        # TODO: implement stream_generate method for this adapter
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
                # response can be a string or an InferenceResponse object
                response_text = response.text if hasattr(response, "text") else response
                if not isinstance(response_text, str):
                    response_text = str(response_text)
                match = re.search(r'\{.*\}', response_text, re.DOTALL)
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
        raise InferenceNotImplementedError("rerank_documents not implemented for this adapter")

    def generate_image(self, prompt: str, style: str = "") -> str:
        """Génère une image à partir d'un prompt et retourne une URL ou Base64."""
        # TODO: implement generate_image method for this adapter
        raise InferenceNotImplementedError("generate_image not implemented for this adapter")

    def generate_sprite(self, prompt: str, style: str = "") -> str:
        """Génère un sprite de personnage (généralement sur fond transparent ou blanc)."""
        return self.generate_image(f"{prompt}, full body portrait on pure white background, anime character sheet style", style)

    def calculate_visual_similarity(self, query: str, item_id: str, media_type: str) -> float:
        """
        Calcule la similarité entre un texte et une image d'un item.
        Fallback par défaut utilisant les embeddings si disponibles.
        """
        try:
            # On tente de récupérer l'embedding du texte
            q_emb = self.get_text_embedding(query)
            if not q_emb:
                return 0.5
                
            # On tente de récupérer l'image via le repository si item_id est fourni
            # Note: Cette implémentation dépend de la capacité de l'adaptateur à accéder aux données.
            # Pour un fallback générique, on peut souvent déléguer à une méthode de recherche visuelle.
            return 0.5 # Valeur neutre par défaut si non surchargeable sans accès repo
        except Exception:
            return 0.5

    def get_text_embedding(self, text: str) -> List[float]:
        """Génère un embedding vectoriel pour un texte donné."""
        # Base stub
        raise InferenceNotImplementedError("get_text_embedding not implemented")

    def get_image_embedding(self, image_data: bytes, model_id: Optional[str] = None) -> List[float]:
        """Génère un embedding vectoriel à partir d'une image."""
        # Base stub - override in adapters supporting vision embeddings
        raise InferenceNotImplementedError("get_image_embedding not implemented")

    def classify_image(self, image_data: bytes, candidate_labels: List[str], model_id: Optional[str] = None) -> Dict[str, float]:
        """Réalise une classification zero-shot d'une image."""
        # Base stub - override in adapters supporting zero-shot vision classification
        raise InferenceNotImplementedError("classify_image not implemented")

    def detect_objects(self, image_data: bytes, candidate_queries: List[str], model_id: Optional[str] = None) -> List[Dict]:
        """Détecte des objets ou attributs dans une image (Open-World Detection)."""
        # Base stub - override in adapters supporting open-world detection
        raise InferenceNotImplementedError("detect_objects not implemented")

    # --- New Methods for Creative Modes ---

    def get_video_temporal_embeddings(self, video_data: bytes) -> List[Dict[str, Any]]:
        """Génère des embeddings pour chaque segment d'une vidéo (Video-RAG)."""
        # TODO: implement get_video_temporal_embeddings method for this adapter
        raise InferenceNotImplementedError("get_video_temporal_embeddings not implemented for this adapter")

    def localize_video_actions(self, video_data: bytes, action_queries: List[str]) -> List[Dict[str, Any]]:
        """Détecte dynamiquement le début et la fin d'actions spécifiques (TAL - Temporal Action Localization)."""
        # Base stub - override in adapters supporting video action localization
        raise InferenceNotImplementedError("localize_video_actions not implemented")

    def transform_image_to_anime(self, image_data: bytes, studio_style: str, prompt: str = "") -> str:
        """Transforme une image réelle en anime via Diffusion + IP-Adapter."""
        # Base stub - override in adapters supporting image-to-anime transformation
        raise InferenceNotImplementedError("transform_image_to_anime not implemented")

    def transform_video_to_anime(self, video_data: bytes, studio_style: str, prompt: str = "") -> str:
        """Applique un Neural Style Transfer SOTA (type FateZero) sur une vidéo avec consistance par attention."""
        # TODO: implement transform_video_to_anime method for this adapter
        raise InferenceNotImplementedError("transform_video_to_anime not implemented for this adapter")

    def generate_soundscape(self, video_metadata: Dict[str, Any], prompt: Optional[str] = None) -> str:
        """Génère une ambiance sonore ou une musique (type AudioLDM) basée sur le contenu d'une vidéo."""
        # TODO: implement generate_soundscape method for this adapter
        raise InferenceNotImplementedError("generate_soundscape not implemented for this adapter")

    def clone_voice(self, text: str, reference_audio: bytes, language: str = "fr") -> bytes:
        """Utilise le Zero-Shot Voice Cloning (RVC) pour synthétiser du texte avec la voix de référence."""
        # TODO: implement clone_voice method for this adapter
        raise InferenceNotImplementedError("clone_voice not implemented for this adapter")

    def speech_to_speech(self, audio_input: bytes, system_prompt: str = "") -> bytes:
        """Passe par un LLM natif multimodal (ex: Qwen2-Audio) pour une interaction End-to-End Voice sans latence TTS."""
        # TODO: implement speech_to_speech method for this adapter
        raise InferenceNotImplementedError("speech_to_speech not implemented for this adapter")

    def estimate_depth(self, image_data: bytes) -> bytes:
        """Estime la carte de profondeur (Depth Map) d'une image 2D (type DepthAnything)."""
        # TODO: implement estimate_depth method for this adapter
        raise InferenceNotImplementedError("estimate_depth not implemented for this adapter")

    def generate_3d_scene(self, image_data: bytes, depth_map: bytes, mode: str = "gaussian_splatting") -> Dict[str, Any]:
        """Génère un espace 3D navigable (Gaussian Splatting / NeRF) à partir d'une image et de sa profondeur, avec in-painting 3D."""
        # TODO: implement generate_3d_scene method for this adapter
        raise InferenceNotImplementedError("generate_3d_scene not implemented for this adapter")

    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]:
        """Segmente les cases et extrait le texte d'une planche de manga (OCR)."""
        # TODO: implement process_manga_page method for this adapter
        raise InferenceNotImplementedError("process_manga_page not implemented for this adapter")

    def translate_manga_page(self, image_data: bytes, target_lang: str = "Français") -> Dict[str, Any]:
        """Détecte, OCR, traduit et redessine le texte dans les bulles d'une page de manga."""
        # TODO: implement translate_manga_page method for this adapter
        raise InferenceNotImplementedError("translate_manga_page not implemented for this adapter")

    def inpaint_text_bubbles(self, image_data: bytes, text_placements: List[Dict]) -> str:
        """Réincruste du texte traduit dans les bulles d'une image (In-painting)."""
        # TODO: implement inpaint_text_bubbles method for this adapter
        raise InferenceNotImplementedError("inpaint_text_bubbles not implemented for this adapter")

    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """Analyse le texte pour détecter du contenu inapproprié ou des spoilers (Guardrail)."""
        categories_str = ", ".join(categories)
        prompt = (
            f"Analyse le texte suivant pour détecter s'il contient du contenu inapproprié "
            f"ou s'il correspond à l'une des catégories suivantes : {categories_str}.\n"
            f"Texte : \"{text}\"\n"
            f"Réponds UNIQUEMENT sous la forme d'un objet JSON contenant ces clés :\n"
            f'{{"is_safe": bool, "detected_categories": [str], "reason": str}}'
        )
        try:
            res = self.generate_structured(
                prompt=prompt,
                response_model=dict,
                system_prompt="Tu es un agent de modération sémantique expert pour une plateforme Anime/Manga."
            )
            is_safe = res.get("is_safe", True)
            detected = res.get("detected_categories", [])
            if not isinstance(detected, list):
                detected = []
            
            return {
                "is_safe": is_safe,
                "detected_categories": detected,
                "action": "block" if not is_safe else "allow",
                "reason": res.get("reason", "Vérification sémantique effectuée.")
            }
        except Exception as e:
            # Fallback par mots-clés de base si le LLM n'est pas configuré, hors ligne ou échoue
            bad_words = ["hentai", "nsfw", "porn", "sex", "gore", "violence extreme"]
            found = [w for w in bad_words if w in text.lower()]
            is_safe = len(found) == 0
            return {
                "is_safe": is_safe,
                "detected_categories": found,
                "action": "block" if not is_safe else "allow",
                "reason": f"Vérification par mots-clés effectuée (Échec LLM: {str(e)})."
            }

    def generate_image_description(self, image_data: bytes, prompt: str = "Décris cette image d'anime de manière très détaillée.") -> str:
        """Utilise un VLM (Visual Language Model) pour générer une description narrative d'une image."""
        # TODO: implement generate_image_description method for this adapter
        raise InferenceNotImplementedError("generate_image_description not implemented for this adapter")

    def generate_video_description(self, video_data: bytes, prompt: str = "Décris cette vidéo d'anime de manière très détaillée.") -> str:
        """Utilise un VLM Vidéo (ex: Video-LLaVA) pour générer une description narrative d'une vidéo."""
        # TODO: implement generate_video_description method for this adapter
        raise InferenceNotImplementedError("generate_video_description not implemented for this adapter")

    def get_diagnostics(self, prompt: str, completion: str) -> Dict[str, Any]:
        """Récupère les données d'activation internes (Logit Lens, Attention) pour l'interprétabilité."""
        # TODO: implement get_diagnostics method for this adapter
        raise InferenceNotImplementedError("get_diagnostics not implemented for this adapter")

    def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]:
        """Calcule la certitude mathématique (entropie, perplexité) d'une génération."""
        # TODO: implement calculate_uncertainty method for this adapter
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
        # TODO: implement visual_rerank method for this adapter
        raise InferenceNotImplementedError("visual_rerank not implemented for this adapter")

    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]:
        """Génère des embeddings multi-vecteurs (type ColBERT/ColEmbed) pour une image."""
        # TODO: implement get_multimodal_late_interaction method for this adapter
        raise InferenceNotImplementedError("get_multimodal_late_interaction not implemented for this adapter")
