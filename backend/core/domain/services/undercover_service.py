import logging
import random
from typing import Dict, List

from .catalog_service import CatalogService
from .similarity_service import SimilarityService

logger = logging.getLogger("animetix.undercover")


class UndercoverService:
    """
    Service gérant la logique spécifique du mode de jeu 'Undercover'.
    """

    def __init__(
        self, catalog_service: CatalogService, similarity_service: SimilarityService
    ):
        self.catalog_service = catalog_service
        self.similarity_service = similarity_service

    def start_game(
        self, media_type: str, difficulty: str, player_ids: List[str], rank_limits: Dict
    ) -> Dict:
        """Initialise une nouvelle partie : choix des mots, rôles et images."""
        catalog = self.catalog_service.get_catalog(media_type)
        if not catalog:
            return {}

        # 1. Sélection du mot Civil (Secret)
        limit = rank_limits.get(media_type, {}).get(difficulty, 300)
        valid = [
            t
            for t in catalog["lookup"][:limit]
            if (t.get("title") or t.get("name")) in catalog["title_to_full_data"]
        ]
        if not valid:
            return {}

        civil_item = random.choice(valid)
        civil_label = civil_item.get("title") or civil_item.get("name")
        civil_id = catalog["title_to_full_data"][civil_label]["id"]

        # 2. Sélection du mot Infiltré (Proche sémantiquement mais différent)
        undercover_title = None
        try:
            similar = self.similarity_service.find_similar_items(
                media_type, str(civil_id), count=10
            )
            # On prend un voisin proche qui n'est pas le mot civil lui-même.
            # find_similar_items peut renvoyer None (item absent du store vectoriel).
            neighbors = (similar or {}).get("metadatas") or [[]]
            options = [
                (m.get("title") or m.get("name"))
                for m in neighbors[0]
                if str(m["id"]) != str(civil_id)
            ]
            if options:
                undercover_title = random.choice(options[:5])
        except Exception as e:
            logger.warning(f"Semantic word selection failed for Undercover: {e}")

        if not undercover_title:
            # Fallback : un mot aléatoire dans le pool
            undercover_title = random.choice(
                [
                    (t.get("title") or t.get("name"))
                    for t in valid
                    if (t.get("title") or t.get("name")) != civil_label
                ]
            )

        # 3. Attribution des rôles
        undercover_player = random.choice(player_ids)
        player_assignments = {}
        for p_id in player_ids:
            role = "Undercover" if p_id == undercover_player else "Civil"
            word_title = undercover_title if role == "Undercover" else civil_label
            item_data = catalog["title_to_full_data"][word_title]

            player_assignments[p_id] = {
                "role": role,
                "word": word_title,
                "image": item_data.get("image"),
            }

        return {
            "civil_word": civil_label,
            "undercover_word": undercover_title,
            "assignments": player_assignments,
        }
