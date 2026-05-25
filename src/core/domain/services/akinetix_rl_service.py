import logging
import numpy as np
import warnings
from typing import List, Dict, Optional, Tuple
from .akinetix_rl_env import AkinetixRLEnvironment
from .catalog_service import CatalogService

logger = logging.getLogger("animetix.rl.service")

# Deprecation Warning
warnings.warn(
    "AkinetixRLDomainService is deprecated and will be removed in a future version. "
    "Please use src.core.domain.services.akinetix_engine.AkinetixEngine instead.",
    DeprecationWarning,
    stacklevel=2
)

class AkinetixRLDomainService:
    """
    DEPRECATED: Service de domaine utilisant l'IA par renforcement pour Akinetix.
    Utilisez AkinetixEngine à la place.
    """
    def __init__(self, catalog_service: CatalogService):
        self.catalog_service = catalog_service
        self._model = None
        self._is_ready = False

    def start_new_game(self, catalog_db: List[Dict]) -> Dict:
        """Initialise une nouvelle partie RL."""
        env = AkinetixRLEnvironment(catalog_db)
        state, info = env.reset()
        
        # Propose la première question (souvent le meilleur gain d'info moyen)
        # On utilise l'index de l'action suggérée par l'env ou une heuristique de départ
        action_idx = self._get_best_action(env)
        next_attr = env.attributes[action_idx]
        
        return {
            'history': [],
            'current_q': self._format_question(next_attr),
            'current_attr': next_attr,
            'game_over': False,
            'ai_guess': None,
            'pool_size': len(env.active_candidates),
            'steps': 0,
            'asked_attrs': []
        }

    def process_answer(self, catalog_db: List[Dict], state: Dict, raw_answer: str) -> Dict:
        """
        Traite la réponse et utilise l'environnement RL pour 
        mener la stratégie de recherche optimale.
        """
        mapping = {'OUI': True, 'NON': False, 'PEUT-ÊTRE': None, 'PROBABLEMENT PAS': None}
        answer_bool = mapping.get(raw_answer.upper())

        # Reconstruire l'état de l'environnement
        env = AkinetixRLEnvironment(catalog_db)
        
        # Restaurer les candidats basés sur l'historique (ou filtrage cumulatif)
        current_attr = state.get('current_attr')
        asked_attrs = state.get('asked_attrs', [])
        if current_attr:
            asked_attrs.append(current_attr)

        # Filtrage manuel pour simuler l'état de l'env (car l'env est sans état persistant ici)
        # En prod, on stockerait les IDs des candidats restants dans la session
        history = state.get('history', [])
        history.append({'q': state.get('current_q'), 'a': raw_answer})

        # Filtrage des candidats
        filtered_candidates = catalog_db
        for h in history:
            attr = state.get('current_attr') # Simplification: on devrait stocker l'attr de chaque Q
            # ... Logique de filtrage plus complexe normalement requise ...
        
        # On délègue à l'environnement pour calculer le prochain état
        # Pour cette implémentation, on va utiliser le gain d'information pur 
        # (ce que le RL apprend à maximiser)
        
        engine_state = env._get_state()
        pool_size = int(engine_state[0])
        steps = state.get('steps', 0) + 1

        new_state = state.copy()
        new_state['history'] = history
        new_state['steps'] = steps
        new_state['asked_attrs'] = asked_attrs

        # Condition de victoire : pool réduit
        # Heuristique : si pool < 5 ou questions > 15, on tente un guess
        if pool_size <= 1 or steps >= 20:
             # Récupérer le meilleur candidat restant
             best_candidate = self._get_best_match(catalog_db, history)
             new_state.update({
                'current_q': f"L'IA prédictive pense à : {best_candidate['title']}",
                'ai_guess': best_candidate['title'],
                'game_over': True
             })
        else:
            action_idx = self._get_best_action(env)
            next_attr = env.attributes[action_idx]
            new_state.update({
                'current_q': self._format_question(next_attr),
                'current_attr': next_attr,
                'pool_size': pool_size
            })

        return new_state

    def _get_best_action(self, env: AkinetixRLEnvironment) -> int:
        """Choisit l'action qui maximise le gain d'information attendu."""
        # Dans un vrai déploiement RL, on ferait self.policy(state)
        # Ici on simule l'agent 'Expert' par recherche gloutonne d'entropie
        best_action = 0
        max_gain = -1
        
        # On sample quelques attributs pour la performance
        sample_size = min(20, len(env.attributes))
        indices = np.random.choice(len(env.attributes), sample_size, replace=False)
        
        for idx in indices:
            # Simuler le gain d'info
            gain = self._simulate_info_gain(env, idx)
            if gain > max_gain:
                max_gain = gain
                best_action = idx
        return best_action

    def _simulate_info_gain(self, env: AkinetixRLEnvironment, action_idx: int) -> float:
        # Heuristique : on préfère les questions qui divisent le pool en deux parts égales
        attr = env.attributes[action_idx]
        attr_type, attr_val = attr.split(':', 1)
        
        count = 0
        for item in env.active_candidates:
            if attr_type == 'genre' and attr_val in item.get('genres', []): count += 1
            elif attr_type == 'tag' and attr_val in item.get('micro_tags', []): count += 1
            elif attr_type == 'studio' and attr_val in item.get('studios', []): count += 1
            
        ratio = count / len(env.active_candidates) if env.active_candidates else 0
        # Gain max à ratio 0.5 (Entropie binaire max)
        return 1.0 - abs(0.5 - ratio)

    def _get_best_match(self, db, history):
        # Fallback simple
        return db[0]

    def _format_question(self, attribute: str) -> str:
        attr_type, val = attribute.split(':', 1)
        if attr_type == 'genre': return f"Est-ce que c'est un {val} ?"
        if attr_type == 'studio': return f"Est-ce que c'est produit par {val} ?"
        if attr_type == 'tag': return f"Est-ce que ça parle de {val} ?"
        return f"Attribut : {val} ?"
