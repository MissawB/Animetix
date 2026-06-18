import re
import logging
from typing import Dict
from ...ports.repository_port import RepositoryPort

logger = logging.getLogger("animetix.similarity")


class SimilarityService:
    """
    Service dédié aux calculs de similarité (vecteurs + métadonnées)
    et à la validation intelligente des titres.
    """

    def __init__(self, repository: RepositoryPort, neo4j_manager=None):
        self.repository = repository
        self.neo4j = neo4j_manager

    def _calculate_graph_similarity(
        self, media_type: str, id_a: str, id_b: str
    ) -> float:
        """
        Calcule une similarité structurelle basée sur le graphe Neo4j.
        Prend en compte les voisins communs (Studios, Créateurs, Thèmes).
        """
        if not self.neo4j:
            return 0.0

        # Requête pour trouver le nombre de nœuds partagés à 1 saut
        query = """
        MATCH (a:Media {id: $id_a})-[:PRODUCED_BY|CREATED_BY|HAS_THEME]->(common)<-[:PRODUCED_BY|CREATED_BY|HAS_THEME]-(b:Media {id: $id_b})
        RETURN count(common) as shared_nodes
        """
        res = self.neo4j.execute_query(query, {"id_a": str(id_a), "id_b": str(id_b)})
        shared_count = res[0]["shared_nodes"] if res else 0

        # Vérification d'une relation directe (Séquelle/Adaptation)
        direct_query = """
        MATCH (a:Media {id: $id_a})-[r:ADAPTED_FROM|SEQUEL_OF]-(b:Media {id: $id_b})
        RETURN count(r) > 0 as has_direct_link
        """
        direct_res = self.neo4j.execute_query(
            direct_query, {"id_a": str(id_a), "id_b": str(id_b)}
        )
        has_direct = direct_res[0]["has_direct_link"] if direct_res else False

        # Normalisation (simplifiée) : 1 nœud commun = 0.2, 5+ = 1.0. Lien direct = bonus immédiat.
        score = min(1.0, shared_count * 0.2)
        if has_direct:
            score = max(score, 0.9)

        return score

    def calculate_similarity(self, media_type: str, item_a: str, item_b: str) -> float:
        """Wrapper pour l'appel au repository."""
        return self.repository.calculate_similarity(media_type, item_a, item_b)

    def calculate_raw_similarity(
        self, media_type: str, secret_title: str, guess_title: str, catalog: Dict
    ) -> float:
        """Calcule la similarité composite (Vecteurs + Graphe)."""
        if secret_title == guess_title:
            return 1.0

        secret_full = catalog["title_to_full_data"].get(secret_title)
        guess_full = catalog["title_to_full_data"].get(guess_title)

        if not secret_full or not guess_full:
            return 0.0

        vec_sim = self.repository.calculate_similarity(
            media_type, str(secret_full["id"]), str(guess_full["id"])
        )
        graph_sim = self._calculate_graph_similarity(
            media_type, str(secret_full["id"]), str(guess_full["id"])
        )

        # Pondération hybride : 70% Vecteur + 30% Graphe
        return (0.7 * vec_sim) + (0.3 * graph_sim)

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
