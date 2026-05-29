import logging
from ....ports.inference_port import InferencePort
from ..prompt_manager import PromptManager

logger = logging.getLogger("animetix.creative.studio_transform")

class StudioTransformService:
    """
    Anime-to-Real Consistency : Transformation d'image et de vidéo.
    Garde l'identité visuelle et assure la consistance temporelle SOTA.
    """
    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager
        self.available_styles = {
            "Shaft": "Style abstrait, inclinaisons de tête, couleurs contrastées.",
            "Ufotable": "Cinématographique, effets de particules, 3D intégrée.",
            "Kyoto": "Détails doux, yeux expressifs, ambiance tranche de vie.",
            "Ghibli": "Aquarelle, nature luxuriante, traits simples et chaleureux."
        }

    def transform_user_to_anime(self, image_data: bytes, studio_name: str) -> str:
        """Applique la transformation de style sur une image fixe."""
        style_description = self.available_styles.get(studio_name, "Anime standard")
        prompt, _ = self.prompt_manager.get_prompt(
            "anime_style_description",
            style_description=style_description
        )
        return self.inference_engine.transform_image_to_anime(
            image_data, 
            studio_style=studio_name, 
            prompt=prompt
        )
        
    def transform_video_to_anime_sota(self, video_data: bytes, studio_name: str) -> str:
        """
        Neural Style Transfer Vidéo SOTA (type FateZero).
        Utilise la consistance par attention pour éviter que les objets ne changent de forme/couleur.
        """
        logger.info(f"🎞️ SOTA Video Style Transfer: Applying {studio_name} style with Attention Consistency...")
        style_description = self.available_styles.get(studio_name, "Anime standard")
        prompt, _ = self.prompt_manager.get_prompt(
            "anime_style_description",
            style_description=style_description
        )
        return self.inference_engine.transform_video_to_anime(
            video_data,
            studio_style=studio_name,
            prompt=prompt
        )
