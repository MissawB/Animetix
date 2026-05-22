from typing import List, Dict, Optional, Tuple, Any
from .akinetix_classical_service import ClassicalAkinetixService
from .catalog_service import CatalogService
from core.ports.game_state_port import GameStatePort

class AkinetixDomainService:
    """
    Service de domaine orchestrant le jeu Akinetix.
    Gère le cycle de vie d'une partie (reset, question, réponse, décision).
    Délégué désormais la gestion des données à CatalogService.
    """
    def __init__(self, catalog_service: CatalogService):
        self.catalog_service = catalog_service

    def start_new_game(self, catalog_db: List[Dict]) -> Dict:
        """Initialise une nouvelle partie et retourne l'état initial."""
        fine_attrs = self.catalog_service.get_akinetix_attributes()
        engine = ClassicalAkinetixService(catalog_db, fine_attributes=fine_attrs)
        next_attr = engine.propose_next_question()
        
        return {
            'history': [],
            'current_q': engine.format_question(next_attr),
            'current_attr': next_attr,
            'game_over': False,
            'ai_guess': None,
            'probs': engine.probs.tolist(),
            'asked_attrs': list(engine.asked_attributes)
        }

    def process_answer(self, catalog_db: List[Dict], state: Dict, raw_answer: str) -> Dict:
        """
        Traite une réponse utilisateur, met à jour les probabilités
        et décide de la suite.
        """
        mapping = {'OUI': 'yes', 'NON': 'no', 'PEUT-ÊTRE': 'probably', 'PROBABLEMENT PAS': 'probably_not'}
        answer = mapping.get(raw_answer.upper(), 'dont_know')
        
        fine_attrs = self.catalog_service.get_akinetix_attributes()
        engine = ClassicalAkinetixService(
            catalog_db, 
            fine_attributes=fine_attrs,
            probs=state.get('probs'),
            asked_attributes=state.get('asked_attrs')
        )
        
        current_attr = state.get('current_attr')
        if current_attr:
            engine.update_probabilities(current_attr, answer)
        
        history = state.get('history', [])
        history.append({'q': state.get('current_q'), 'a': raw_answer})
        
        best_title, best_prob = engine.get_best_guess()
        steps = len(engine.asked_attributes)
        
        new_state = state.copy()
        new_state['history'] = history
        new_state['probs'] = engine.probs.tolist()
        new_state['asked_attrs'] = list(engine.asked_attributes)

        if (best_prob > 0.8 and steps >= 5) or steps >= 25:
            new_state.update({
                'current_q': f"Est-ce que tu penses à : {best_title} ?", 
                'ai_guess': best_title, 
                'game_over': True
            })
        else:
            next_attr = engine.propose_next_question()
            new_state.update({
                'current_q': engine.format_question(next_attr),
                'current_attr': next_attr
            })
            
        return new_state

    def get_state(self, port: GameStatePort) -> dict[str, Any]:
        """Loads Akinetix-specific state from the port."""
        return {
            'history': port.get('akinetix_history', []),
            'current_q': port.get('akinetix_current_q'),
            'current_attr': port.get('akinetix_current_attr'),
            'game_over': port.get('akinetix_game_over', False),
            'ai_guess': port.get('akinetix_ai_guess'),
            'probs': port.get('akinetix_probs'),
            'asked_attrs': port.get('akinetix_asked_attrs'),
            'is_daily': port.get('is_daily', False)
        }

    def save_state(self, port: GameStatePort, state: dict[str, Any]) -> None:
        """Saves Akinetix-specific state back to the port."""
        port.update({
            'akinetix_history': state.get('history'),
            'akinetix_current_q': state.get('current_q'),
            'akinetix_current_attr': state.get('current_attr'),
            'akinetix_game_over': state.get('game_over', False),
            'akinetix_ai_guess': state.get('ai_guess'),
            'akinetix_probs': state.get('probs'),
            'akinetix_asked_attrs': state.get('asked_attrs'),
            'is_daily': state.get('is_daily', False)
        })
    
    def reset_state(self, port: GameStatePort) -> None:
        """Clears Akinetix state in the port."""
        port.update({
            'akinetix_history': [],
            'akinetix_current_q': None,
            'akinetix_current_attr': None,
            'akinetix_game_over': False,
            'akinetix_ai_guess': None,
            'akinetix_probs': None,
            'akinetix_asked_attrs': None,
            'is_daily': False
        })
