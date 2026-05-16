import logging
from typing import Optional, List, Dict, Any
from core.ports.inference_port import InferencePort

logger = logging.getLogger("animetix.orchestration")

class MultimodalOrchestrator:
    """
    Façade unifiée pour orchestrer les capacités IA du système.
    Délègue les tâches complexes aux adaptateurs via InferencePort.
    """
    def __init__(self, inference_adapter: InferencePort):
        self.adapter = inference_adapter

    def analyze_video_content(self, video_data: bytes, queries: List[str]) -> List[Dict[str, Any]]:
        """Orchestre l'analyse temporelle et l'action locale d'une vidéo."""
        try:
            temporal_embeddings = self.adapter.get_video_temporal_embeddings(video_data)
            actions = self.adapter.localize_video_actions(video_data, queries)
            return {"embeddings": temporal_embeddings, "actions": actions}
        except Exception as e:
            logger.error(f"Error orchestrating video analysis: {e}")
            return {"error": str(e)}

    def transform_to_anime(self, image_data: bytes, style: str, prompt: str = "") -> Optional[str]:
        """Orchestre la transformation d'image avec vérification de sécurité."""
        try:
            # Check moderation before processing
            mod = self.adapter.moderate_content(prompt, ["safety"])
            if not mod.get("is_safe", True):
                logger.warning("Transformation prompt rejected by guardrail.")
                return None
            return self.adapter.transform_image_to_anime(image_data, style, prompt)
        except Exception as e:
            logger.error(f"Error orchestrating anime transformation: {e}")
            return None

    def generate_scene_description(self, image_data: bytes) -> str:
        """Utilise le VLM pour générer une description narrative."""
        try:
            return self.adapter.generate_image_description(image_data)
        except Exception as e:
            logger.error(f"Error generating scene description: {e}")
            return "Une erreur est survenue lors de l'analyse visuelle."

    def extract_manga_data(self, image_data: bytes) -> Dict[str, Any]:
        """Orchestre le traitement OCR et l'in-painting des bulles."""
        try:
            data = self.adapter.process_manga_page(image_data)
            # Potentiellement lancer d'autres tâches ici
            return data
        except Exception as e:
            logger.error(f"Error extracting manga data: {e}")
            return {"error": str(e)}
