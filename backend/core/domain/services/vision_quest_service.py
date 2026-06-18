import random
from typing import Dict, Optional
from ...ports.inference_port import InferencePort
from .advanced_vision_service import AdvancedVisionService


class VisionQuestDomainService:
    def __init__(
        self,
        inference_engine: InferencePort,
        vision_service: Optional[AdvancedVisionService] = None,
    ):
        self.inference_engine = inference_engine
        self.vision_service = vision_service

    def select_secret(self, catalog: Dict) -> Optional[Dict]:
        """Sélectionne une œuvre aléatoire avec image pour le défi visuel."""
        valid_items = [item for item in catalog.get("db", []) if item.get("image")]
        if not valid_items:
            return None
        return random.choice(valid_items[:300])

    def get_image_style_info(self, image_data: bytes) -> str:
        """Identifie le style de l'image pour donner des indices."""
        if self.vision_service:
            return self.vision_service.identify_artist_style(image_data)
        return "Inconnu"

    def calculate_score(
        self, query: str, secret_id: str, secret_title: str, media_type: str
    ) -> float:
        """Calcule le score de similarité visuelle entre la description et l'image."""
        score = self.inference_engine.calculate_visual_similarity(
            query, secret_id, media_type
        )

        # Bonus : si l'utilisateur cite le titre (et que la similarité est déjà bonne)
        if secret_title.lower() in query.lower() and score > 85:
            return 100.0

        return score

    def check_victory(self, score: float) -> bool:
        """Définit le seuil de victoire pour ce mode."""
        return score >= 95.0
