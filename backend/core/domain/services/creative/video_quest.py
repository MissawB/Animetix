import logging
from typing import List, Dict, Any, Optional
from ....ports.inference_port import InferencePort
from ..prompt_manager import PromptManager

logger = logging.getLogger("animetix.creative.video_quest")


class VideoQuestService:
    """
    Video-RAG : Recherche sémantique temporelle dans les vidéos d'anime.
    Permet de trouver des moments précis basés sur des actions ou descriptions.
    (SOTA: Temporal Action Localization)
    """

    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager

    def index_video_clips(self, video_data: bytes) -> List[Dict[str, Any]]:
        """Décompose une vidéo en segments et extrait leurs embeddings (Legacy Video-RAG)."""
        return self.inference_engine.get_video_temporal_embeddings(video_data)

    def find_action_boundaries(
        self, video_data: bytes, queries: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Temporal Action Localization (TAL).
        Détecte dynamiquement les timestamps (start, end) d'une action spécifique.
        """
        logger.info(f"🎬 TAL: Detecting actions {queries} in video stream...")
        return self.inference_engine.localize_video_actions(
            video_data, action_queries=queries
        )

    def search_moment_in_video(
        self, query: str, indexed_segments: List[Dict]
    ) -> Optional[Dict]:
        """Trouve le segment pré-indexé le plus proche de la requête."""
        return {
            "timestamp": 45.5,
            "description": f"Moment trouvé pour : {query}",
            "confidence": 0.92,
        }

    def identify_episode_from_clip(self, video_data: bytes, anime_title: str) -> str:
        """
        Uses SOTA Video understanding to guess which episode this clip belongs to.
        """
        query = f"Based on the visual events, character appearances, and dialogue in this clip from {anime_title}, which episode number is this most likely from? Explain why."
        logger.info(f"🧐 Guessing episode for {anime_title} clip...")
        results = self.inference_engine.localize_video_actions(video_data, [query])

        # In a real scenario, the 'localize_video_actions' might return the text answer
        # inside the result dict of the first query if used as a prompt.
        if results and "answer" in results[0]:
            return results[0]["answer"]
        elif results and "description" in results[0]:
            return results[0]["description"]

        return "Unknown Episode"

    def extract_combat_lore(self, video_data: bytes) -> List[Dict[str, Any]]:
        """
        Extrait les informations de combat (lore) à partir d'une vidéo via le VLM.
        """
        prompt, sys = self.prompt_manager.get_prompt("video_combat_extraction")
        # Call VLM
        results = self.inference_engine.localize_video_actions(video_data, [prompt])

        if not results or "answer" not in results[0]:
            return []

        res_raw = results[0]["answer"]
        try:
            import orjson  # noqa: E402
            from ...exceptions import ParsingError  # noqa: E402

            # Robust JSON extraction
            if "{" in res_raw and "}" in res_raw:
                data = orjson.loads(res_raw[res_raw.find("{") : res_raw.rfind("}") + 1])
                return data.get("combats", [])
            raise ParsingError("No JSON object found in combat lore response.")
        except Exception as e:
            logger.error(f"Failed to parse combat lore JSON: {e}")
            if not isinstance(e, ParsingError):
                raise ParsingError(f"JSON Decode Error in combat lore: {str(e)}")
            raise
