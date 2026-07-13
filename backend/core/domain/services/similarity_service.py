import logging
import re
from typing import Dict, Optional

from ...ports.repository_port import RepositoryPort

logger = logging.getLogger("animetix.similarity")


class SimilarityService:
    """
    Service dédié aux calculs de similarité (vecteurs + métadonnées)
    et à la validation intelligente des titres.
    """

    def __init__(self, repository: RepositoryPort):
        self.repository = repository

    def calculate_similarity(self, media_type: str, item_a: str, item_b: str) -> float:
        """Wrapper pour l'appel au repository."""
        return self.repository.calculate_similarity(media_type, item_a, item_b)

    def calculate_raw_similarity(
        self, media_type: str, secret_title: str, guess_title: str, catalog: Dict
    ) -> float:
        """Similarité vectorielle brute entre deux œuvres.

        Ce n'est PLUS ce qui note le jeu classique : mesuré sur le vrai catalogue, le
        cosinus des embeddings de description a un plancher de bruit à 0,583 entre deux
        œuvres sans rapport, et il classait Kimetsu plus proche de Death Note que Monster.
        La proximité du jeu vit désormais dans `ProximityService`. Ceci sert la recherche
        sémantique, où le voisinage flou est un atout et non un mensonge.
        """
        if secret_title == guess_title:
            return 1.0

        secret_full = catalog["title_to_full_data"].get(secret_title)
        guess_full = catalog["title_to_full_data"].get(guess_title)
        if not secret_full or not guess_full:
            return 0.0

        return self.repository.calculate_similarity(
            media_type, str(secret_full["id"]), str(guess_full["id"])
        )

    def find_similar_items(
        self, media_type: str, item_id: str, count: int = 5
    ) -> Optional[Dict]:
        """Voisins sémantiques d'un item via la recherche vectorielle du repository.

        Retourne le résultat brut du store vectoriel (format pgvector :
        ``{"metadatas": [[...]], "distances": [[...]], ...}``) ou ``None`` si
        l'item est introuvable. Comme :meth:`calculate_similarity`, ``media_type``
        sert directement de nom de collection.
        """
        return self.repository.get_nearest_neighbors(media_type, str(item_id), count)

    def check_title_match(self, user_input: str, media_item: Dict) -> bool:
        """Vérifie si la saisie utilisateur correspond aux titres ou synonymes de l'œuvre."""
        if not user_input or not media_item:
            return False

        def normalize(t):
            if not t:
                return ""
            t = t.lower().strip()
            t = re.sub(r"[^a-z0-9\s]", "", t)
            return " ".join(t.split())

        norm_input = normalize(user_input)
        if not norm_input:
            return False

        targets = [
            media_item.get("title"),
            media_item.get("title_english"),
            media_item.get("title_native"),
            media_item.get("name"),
            *media_item.get("alternative_titles", []),
        ]

        meta = media_item.get("metadata", {})
        if isinstance(meta, dict):
            targets.extend(meta.get("synonyms", []))
            targets.extend(meta.get("alternative_titles", []))

        for target in targets:
            if target and norm_input == normalize(target):
                return True

        # Cas spécifique : SNK pour Shingeki no Kyojin
        shingeki_check = (
            normalize(media_item.get("title", ""))
            + " "
            + normalize(media_item.get("title_native", ""))
        )
        if norm_input == "snk" and "shingeki" in shingeki_check:
            return True

        return False
