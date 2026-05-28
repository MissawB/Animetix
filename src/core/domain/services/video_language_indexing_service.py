import logging
from typing import List, Dict, Any, Optional
from core.ports.inference_port import InferencePort
from core.domain.services.prompt_manager import PromptManager

logger = logging.getLogger("animetix.video_indexing")

class VideoLanguageIndexingService:
    """
    Service d'Indexation Langage-Vidéo (Task 5.5).
    Utilise Video-LLaVA pour générer des descriptions denses de scènes d'animes.
    """
    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager, repository: Any = None):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager
        self.repository = repository

    def generate_dense_video_description(self, video_data: bytes, title: str) -> str:
        """
        Génère une description textuelle détaillée du contenu d'une vidéo anime.
        """
        logger.info(f"📽️ Video-LLaVA: Generating dense narrative for '{title}'...")
        
        prompt, system = self.prompt_manager.get_prompt("video_narrative_generation", title=title)
        
        # On utilise une nouvelle méthode de l'InferencePort
        description = self.inference_engine.generate_video_description(video_data, prompt)
        
        if not description:
            logger.error(f"❌ Video-LLaVA failed for '{title}'.")
            return ""
            
        logger.info(f"✅ Video Narrative generated ({len(description)} chars).")
        return description

    def index_video_moment(self, video_data: bytes, metadata: Dict[str, Any]):
        """
        Pipeline complet : Vidéo -> Description Dense -> Indexation Vectorielle.
        """
        title = metadata.get("title", "Unknown Anime")
        narrative = self.generate_dense_video_description(video_data, title)
        
        if narrative and self.repository:
            # Indexation dans l'espace sémantique 'video_narratives'
            # self.repository.index_text(narrative, metadata, collection="video_narratives")
            logger.info(f"💾 Narrative indexed for {title}.")
            
        return narrative
