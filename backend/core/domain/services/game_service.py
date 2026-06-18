import logging
import random
from typing import Dict, List, Optional

from ...ports.repository_port import RepositoryPort
from .catalog_service import CatalogService
from .similarity_service import SimilarityService
from .undercover_service import UndercoverService

logger = logging.getLogger("animetix.game")


class GameService:
    """
    Service central pour la logique des jeux Animetix (Game Engine).
    Orchestre les sous-services spécialisés (Catalog, Similarity, Undercover).
    """

    def __init__(
        self,
        repository: RepositoryPort,
        catalog_service: CatalogService,
        similarity_service: Optional[SimilarityService] = None,
        undercover_service: Optional[UndercoverService] = None,
    ):
        self.repository = repository
        self.catalog_service = catalog_service
        self.similarity_service = similarity_service or SimilarityService(repository)
        self.undercover_service = undercover_service or UndercoverService(
            catalog_service, self.similarity_service
        )

    def get_catalog(self, media_type: str) -> Dict:
        """Délégation au CatalogService."""
        return self.catalog_service.get_catalog(media_type)

    def calculate_raw_similarity(
        self, media_type: str, secret_title: str, guess_title: str, catalog: Dict
    ) -> float:
        """Délégation au SimilarityService."""
        return self.similarity_service.calculate_raw_similarity(
            media_type, secret_title, guess_title, catalog
        )

    def select_secret(self, media_type: str, difficulty: str, rank_limits: Dict) -> str:
        """Sélectionne un titre secret basé sur la difficulté (popularité)."""
        catalog = self.get_catalog(media_type)
        if not catalog:
            return ""

        limit = rank_limits.get(media_type, {}).get(difficulty, 300)
        valid_lookup = catalog.get("lookup", [])[:limit]
        valid_titles = [
            item.get("title") or item.get("name")
            for item in valid_lookup
            if (item.get("title") or item.get("name"))
            in catalog.get("title_to_full_data", {})
        ]

        if not valid_titles:
            valid_titles = catalog.get("titles", [])[:50]

        return random.choice(valid_titles) if valid_titles else ""

    def select_secret_custom(self, media_type: str, config: Dict, catalog: Dict) -> str:
        """Sélectionne un titre secret basé sur des filtres personnalisés (genres, tags)."""
        mode = config.get("mode", "all")
        whitelist, blacklist = config.get("whitelist", []), config.get("blacklist", [])
        g_white, g_black = (
            config.get("genres_white", []),
            config.get("genres_black", []),
        )
        t_white, t_black = config.get("tags_white", []), config.get("tags_black", [])

        pool = (
            [
                catalog["title_to_full_data"][t]
                for t in whitelist
                if t in catalog["title_to_full_data"]
            ]
            if (mode == "white" and whitelist)
            else [
                item
                for item in catalog["db"]
                if (item.get("title") or item.get("name")) not in blacklist
            ]
        )

        filtered_pool = []
        for item in pool:
            item_genres, item_tags = (
                set(item.get("genres", [])),
                set(item.get("tags", [])),
            )
            if any(g in item_genres for g in g_black) or any(
                t in item_tags for t in t_black
            ):
                continue
            if (g_white or t_white) and not (
                any(g in item_genres for g in g_white)
                or any(t in item_tags for t in t_white)
            ):
                continue
            filtered_pool.append(item)

        if not filtered_pool:
            filtered_pool = catalog["db"][:50]
        if not filtered_pool:
            return ""

        secret_obj = random.choice(filtered_pool)
        return secret_obj.get("title") or secret_obj.get("name")

    def start_undercover_game(
        self, media_type: str, difficulty: str, player_ids: List[str], rank_limits: Dict
    ) -> Dict:
        """Délégation au UndercoverService."""
        return self.undercover_service.start_game(
            media_type, difficulty, player_ids, rank_limits
        )

    def calculate_similarity(
        self, media_type: str, item_a_id: str, item_b_id: str
    ) -> float:
        """Délégation au SimilarityService."""
        return self.similarity_service.calculate_similarity(
            media_type, item_a_id, item_b_id
        )

    def find_similar_items(
        self, media_type: str, item_id: str, count: int = 5
    ) -> Optional[Dict]:
        """Délégation au SimilarityService."""
        return self.similarity_service.find_similar_items(media_type, item_id, count)

    def check_title_match(self, user_input: str, media_item: Dict) -> bool:
        """Délégation au SimilarityService."""
        return self.similarity_service.check_title_match(user_input, media_item)
