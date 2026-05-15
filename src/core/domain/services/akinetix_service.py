from typing import List, Dict, Optional, Tuple
from .akinetix_classical_service import ClassicalAkinetixService
from .catalog_service import CatalogService

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
