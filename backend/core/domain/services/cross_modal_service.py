import logging
from typing import Dict, List, Optional

import numpy as np
from core.domain.exceptions import SearchIndexUnavailableError
from core.domain.services.prompt_manager import PromptManager
from core.ports.inference_port import InferencePort

logger = logging.getLogger("animetix.cross_modal")


class CrossModalSearchService:
    """
    RAG Cross-Modal (Deep Multimodality).
    """

    # `unified_clip_space` a aujourd'hui zéro pipeline d'écriture accessible
    # à un utilisateur normal (voir docs/analysis/2026-07-13-pgvector-consumers.md
    # §2.1) : interroger cette collection ne peut jamais retourner de résultat
    # tant qu'elle est vide.
    COLLECTION_NAME = "unified_clip_space"

    def __init__(self, inference_engine: InferencePort, vector_db):
        self.inference_engine = inference_engine
        self.vector_db = vector_db

    def is_available(self) -> bool:
        """True si la collection cible contient au moins un vecteur.

        Garde-fou anti-facturation : à appeler par le caller (vue) AVANT
        toute déduction de Berrix, pas seulement avant la recherche.
        """
        return self.vector_db.get_collection_count(self.COLLECTION_NAME) > 0

    def deep_multimodal_search(
        self, text_query: str, image_data: Optional[bytes] = None, limit: int = 10
    ) -> List[Dict]:
        """
        Effectue une recherche en fusionnant les intentions texte et image.
        """
        if not self.is_available():
            raise SearchIndexUnavailableError(
                f"La collection '{self.COLLECTION_NAME}' est vide : "
                "recherche cross-modale impossible."
            )

        logger.info(
            f"🌉 Cross-Modal Search: Fusioning text '{text_query}' and image data..."
        )

        # ... (rest of logic)

        text_vec = []
        if text_query:
            # Pas de repli sur un vecteur aléatoire : un échec d'embedding
            # doit être visible (l'appelant reçoit l'exception), jamais
            # transformé en résultat de recherche à l'apparence plausible
            # mais en réalité tiré au hasard.
            text_vec = self.inference_engine.get_text_embedding(text_query)

        image_vec = []
        if image_data:
            image_vec = self.inference_engine.get_image_embedding(
                image_data, model_id="dudcjs2779/anime-style-tag-clip"
            )

        # 2. Fusion des Vecteurs (Weighted Average ou Projection)
        if len(text_vec) > 0 and len(image_vec) > 0:
            # Alpha: importance du texte vs image (ex: 0.5)
            final_vec = (0.5 * np.array(text_vec)) + (0.5 * np.array(image_vec))
        elif len(text_vec) > 0:
            final_vec = np.array(text_vec)
        else:
            final_vec = np.array(image_vec)

        # 3. Recherche dans pgvector avec le vecteur fusionné
        # Note: On suppose que la collection contient des embeddings CLIP
        results = self.vector_db.search_by_vector(
            "unified_clip_space", final_vec.tolist(), limit=limit
        )

        return results


class VlmIndexingService:
    """
    VLM para-Indexing.
    Utilise Llava/Idefics pour décrire visuellement le catalogue et indexer ces récits.
    """

    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager

    def describe_poster(self, image_data: bytes, title: str) -> str:
        """Génère une description textuelle riche du contenu visuel."""
        prompt, system = self.prompt_manager.get_prompt(
            "cross_modal_analysis", title=title
        )
        description = self.inference_engine.generate_image_description(
            image_data, prompt
        )
        return description

    def index_visual_narrative(self, media_item: Dict, image_data: bytes):
        """Pipeline d'indexation : Image -> Texte VLM -> pgvector."""
        narrative = self.describe_poster(image_data, media_item["title"])
        logger.info(f"📸 VLM Narrative for {media_item['title']}: {narrative[:100]}...")
        # L'indexation finale se fait dans pgvector (non implémenté ici car dépend de l'adapter)
        return narrative
