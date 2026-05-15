import re
import logging
from typing import Dict, Optional, List
from ...ports.repository_port import RepositoryPort

logger = logging.getLogger('animetix.similarity')

class SimilarityService:
    """
    Service dédié aux calculs de similarité (vecteurs + métadonnées)
    et à la validation intelligente des titres.
    """
    def __init__(self, repository: RepositoryPort):
        self.repository = repository

    def calculate_similarity(self, media_type: str, item_a_id: str, item_b_id: str) -> float:
        """Calcul direct de la distance cosinus entre deux vecteurs en base."""
        coll_map = {'Anime': 'anime_thematic', 'Manga': 'manga_thematic', 'Character': 'character_vibe'}
        coll_name = coll_map.get(media_type)
        if not coll_name: return 0.0
        return self.repository.calculate_similarity(coll_name, item_a_id, item_b_id)

    def find_similar_items(self, media_type: str, item_id: str, count: int = 5) -> Optional[Dict]:
        """Récupère les voisins les plus proches via recherche vectorielle."""
        coll_map = {'Anime': 'anime_thematic', 'Manga': 'manga_thematic', 'Character': 'character_vibe'}
        coll_name = coll_map.get(media_type)
        if not coll_name: return None
        return self.repository.get_nearest_neighbors(coll_name, item_id, n_results=count)

    def calculate_raw_similarity(self, media_type: str, secret_title: str, guess_title: str, catalog: Dict) -> float:
        """Calcule la similarité composite (Vecteurs + Business Logic)."""
        if secret_title == guess_title:
            return 1.0
            
        secret_full = catalog['title_to_full_data'].get(secret_title)
        guess_full = catalog['title_to_full_data'].get(guess_title)
        
        if not secret_full or not guess_full:
            return 0.0
            
        vec_sim = self.calculate_similarity(media_type, str(secret_full['id']), str(guess_full['id']))
        
        if media_type == 'Character':
            # Pondération : 70% Vecteur (vibe) + 30% Affiliations (logique)
            org_S = set(secret_full.get('metadata', {}).get('affiliations', []))
            org_G = set(guess_full.get('metadata', {}).get('affiliations', []))
            org_intersection = org_S.intersection(org_G)
            org_sim = 1.0 if len(org_intersection) > 0 else 0.0
            return (0.7 * vec_sim) + (0.3 * org_sim)
        
        return vec_sim

    def check_title_match(self, user_input: str, media_item: Dict) -> bool:
        """Vérifie si la saisie utilisateur correspond aux titres ou synonymes de l'œuvre."""
        if not user_input or not media_item: return False
        
        def normalize(t):
            if not t: return ""
            t = t.lower().strip()
            t = re.sub(r'[^a-z0-9\s]', '', t)
            return " ".join(t.split())

        norm_input = normalize(user_input)
        if not norm_input: return False

        targets = [
            media_item.get('title'),
            media_item.get('title_english'),
            media_item.get('title_native'),
            media_item.get('name'),
            *media_item.get('alternative_titles', [])
        ]
        
        meta = media_item.get('metadata', {})
        if isinstance(meta, dict):
            targets.extend(meta.get('synonyms', []))
            targets.extend(meta.get('alternative_titles', []))

        for target in targets:
            if target and norm_input == normalize(target):
                return True
                
        # Cas spécifique : SNK pour Shingeki no Kyojin
        shingeki_check = normalize(media_item.get('title', '')) + " " + normalize(media_item.get('title_native', ''))
        if norm_input == "snk" and "shingeki" in shingeki_check:
            return True
            
        return False
