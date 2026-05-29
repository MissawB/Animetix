import logging
from .video_quest import VideoQuestService
from ....ports.inference_port import InferencePort
from ..prompt_manager import PromptManager

logger = logging.getLogger("animetix.creative.soundscape")

class SoundscapeGenerationService:
    """
    Video-to-Audio (Soundscape Generation).
    Utilise AudioLDM pour générer automatiquement une ambiance sonore à partir d'une vidéo muette.
    """
    def __init__(self, inference_engine: InferencePort, video_service: VideoQuestService, prompt_manager: PromptManager):
        self.inference_engine = inference_engine
        self.video_service = video_service
        self.prompt_manager = prompt_manager

    def generate_soundscape_for_video(self, video_data: bytes) -> str:
        """
        Génère une bande son cohérente avec le contenu visuel de la vidéo.
        """
        logger.info("🎵 Soundscape: Analyzing video content for audio generation...")
        
        # 1. Analyse du contenu via Video-RAG (via l'adaptateur inference)
        # On utilise les nouvelles méthodes de port d'inférence pour une analyse réelle
        actions = self.inference_engine.localize_video_actions(video_data, ["combat", "pluie", "magie"])
        description = self.inference_engine.generate_image_description(video_data[:1024*10]) # Premier frame
        
        analysis = {
            "scene": description,
            "detected_actions": actions,
            "vibe": "Epique et cinématique"
        }
        
        # 2. Construction du prompt audio via PromptManager
        audio_prompt, _ = self.prompt_manager.get_prompt(
            "soundscape_generation",
            scene=analysis['scene'],
            actions=str(analysis['detected_actions'])
        )
        
        # 3. Génération via l'engine AudioLDM
        return self.inference_engine.generate_soundscape(video_metadata=analysis, prompt=audio_prompt)
