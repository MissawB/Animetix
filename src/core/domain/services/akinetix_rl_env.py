import math
import random
from typing import List, Dict, Any, Tuple
import numpy as np

class AkinetixRLEnvironment:
    """
    Environnement simulé pour l'apprentissage par renforcement (RL) du mode Akinetix.
    Modélise le jeu comme un Processus de Décision Markovien (MDP).
    Compatible avec l'API OpenAI Gym/Gymnasium en principe.
    """
    def __init__(self, catalog_db: List[Dict]):
        self.catalog = catalog_db
        # Attributs possibles pour poser des questions (Action Space)
        self.attributes = self._extract_all_attributes(catalog_db)
        self.reset()

    def _extract_all_attributes(self, db: List[Dict]) -> List[str]:
        """Extrait tous les genres, tags et studios possibles pour former l'espace d'action."""
        attrs = set()
        for item in db:
            attrs.update([f"genre:{g}" for g in item.get('genres', [])])
            attrs.update([f"tag:{t}" for t in item.get('micro_tags', [])])
            attrs.update([f"studio:{s}" for s in item.get('studios', [])])
        return list(attrs)

    def reset(self) -> Tuple[np.ndarray, Dict]:
        """Réinitialise l'environnement pour une nouvelle partie."""
        self.target_item = random.choice(self.catalog)
        self.active_candidates = self.catalog.copy()
        self.asked_questions = set()
        self.steps = 0
        return self._get_state(), {"target": self.target_item['title']}

    def _get_state(self) -> np.ndarray:
        """
        Représentation de l'état (State Space).
        Dans un vrai réseau de neurones, on passerait les probabilités/entropies
        ou les embeddings du pool de candidats restants.
        Ici on retourne un vecteur simplifié : [taille_du_pool, entropie_moyenne, étapes_écoulées]
        """
        pool_size = len(self.active_candidates)
        entropy = self._calculate_entropy()
        return np.array([pool_size, entropy, self.steps], dtype=np.float32)

    def _calculate_entropy(self) -> float:
        """Calcule l'entropie de Shannon de l'espace de recherche actuel."""
        if not self.active_candidates: return 0.0
        # Simulation d'entropie basée sur la distribution des attributs restants
        p = 1.0 / len(self.active_candidates)
        return -sum(p * math.log2(p) for _ in self.active_candidates)

    def step(self, action_idx: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        Exécute une action (poser une question sur un attribut précis).
        Retourne : state, reward, terminated, truncated, info
        """
        self.steps += 1
        attribute = self.attributes[action_idx]
        self.asked_questions.add(attribute)
        
        attr_type, attr_val = attribute.split(':', 1)
        
        # Le "vrai" Akinator répond selon l'item cible
        answer = False
        if attr_type == 'genre': answer = attr_val in self.target_item.get('genres', [])
        elif attr_type == 'tag': answer = attr_val in self.target_item.get('micro_tags', [])
        elif attr_type == 'studio': answer = attr_val in self.target_item.get('studios', [])

        # Filtrage de l'espace de recherche
        previous_size = len(self.active_candidates)
        new_candidates = []
        for item in self.active_candidates:
            item_has_attr = False
            if attr_type == 'genre': item_has_attr = attr_val in item.get('genres', [])
            elif attr_type == 'tag': item_has_attr = attr_val in item.get('micro_tags', [])
            elif attr_type == 'studio': item_has_attr = attr_val in item.get('studios', [])
            
            if item_has_attr == answer:
                new_candidates.append(item)
                
        self.active_candidates = new_candidates
        new_size = len(self.active_candidates)

        # RL Reward Shaping (Optimisation du gain d'information)
        reward = -0.1 # Pénalité pour chaque étape (incite à la rapidité)
        
        # Récompense basée sur la réduction de l'espace (Information Gain)
        information_gain = (previous_size - new_size) / previous_size
        reward += information_gain * 0.5
        
        terminated = False
        if new_size == 1:
            terminated = True
            if self.active_candidates[0]['id'] == self.target_item['id']:
                reward += 10.0 # Victoire
            else:
                reward -= 5.0 # Faux positif
        elif new_size == 0:
            terminated = True
            reward -= 10.0 # Échec total
            
        truncated = self.steps >= 20 # Limite de questions

        return self._get_state(), reward, terminated, truncated, {"information_gain": information_gain}

class AkinetixRLService:
    def __init__(self, catalog_service):
        self.catalog_service = catalog_service

    def create_env(self, media_type: str) -> AkinetixRLEnvironment:
        catalog = self.catalog_service.load_catalog(media_type)
        return AkinetixRLEnvironment(catalog['db'])
