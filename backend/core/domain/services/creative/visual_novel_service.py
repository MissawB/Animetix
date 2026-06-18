from typing import Optional, Dict
import logging
from ...entities.ai_schemas import VNScript, VNScene
from ..llm_service import LLMService
from ....ports.repository_port import RepositoryPort

logger = logging.getLogger("animetix.creative.visual_novel")


class VisualNovelService:
    """Service for generating Visual Novel scripts from creative fusions."""

    def __init__(self, llm_service: LLMService, repository: RepositoryPort):
        self.llm_service = llm_service
        self.repository = repository

    def generate_script(self, fusion_id: int) -> Optional[VNScript]:
        """
        Generates a structured Visual Novel script based on an existing creative fusion.
        """
        logger.info(f"Generating VN script for fusion ID: {fusion_id}")

        # 1. Fetch fusion data from the repository
        fusion_data = self.repository.get_creative_fusion(fusion_id)
        if not fusion_data:
            logger.error(f"Fusion with ID {fusion_id} not found.")
            return None

        # 2. Prepare context for the prompt
        fusion_details = (
            f"Crossover between {fusion_data.get('title_a')} and {fusion_data.get('title_b')}.\n"
            f"Scenario: {fusion_data.get('scenario_text')}\n"
            f"Art Style: {fusion_data.get('art_style')}"
        )

        # 3. Get prompt from the manager
        prompt, system = self.llm_service.prompt_manager.get_prompt(
            "vn_script_generation", fusion_id=fusion_id, fusion_details=fusion_details
        )

        # 4. Generate structured script using LLMService
        try:
            script = self.llm_service.generate_structured(
                prompt, VNScript, system_prompt=system
            )
            return script
        except Exception as e:
            logger.error(f"VN script generation failed: {e}")
            return None

    def generate_scene_assets(
        self, scene: VNScene, session_seed: int
    ) -> Dict[str, str]:
        """
        Génère les assets visuels (sprite et background) pour une scène donnée.
        """
        logger.info(
            f"Generating visual assets for scene: {scene.character} ({scene.mood})"
        )

        # Utilisation du vision_engine de l'LLMService
        engine = self.llm_service.vision_engine

        # On peut passer le session_seed si l'adaptateur le supporte (pas encore le cas ici)
        # Mais on respecte l'intention de consistance.

        sprite_url = engine.generate_sprite(
            f"{scene.character}, {scene.mood} expression"
        )
        background_url = engine.generate_image(scene.bg_prompt)

        return {"sprite_url": sprite_url, "background_url": background_url}
