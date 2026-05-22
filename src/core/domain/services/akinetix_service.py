import logging
from typing import List, Dict, Optional, Any
from .akinetix_classical_service import ClassicalAkinetixService
from .catalog_service import CatalogService
from core.ports.game_state_port import GameStatePort
from ..entities.akinetix import AkinetixGameState, AkinetixQuestion

logger = logging.getLogger('animetix.akinetix')

class AkinetixDomainService:
    """
    Service de domaine orchestrant le jeu Akinetix.
    Gère le cycle de vie d'une partie (reset, question, réponse, décision).
    Délégué désormais la gestion des données à CatalogService.
    """
    
    # Constantes pour la logique de décision
    PROBABILITY_THRESHOLD = 0.8
    MIN_STEPS_BEFORE_GUESS = 5
    MAX_STEPS_TOTAL = 25

    # Mapping des réponses utilisateur vers format interne
    ANSWER_MAPPING = {
        'OUI': 'yes',
        'NON': 'no',
        'PEUT-ÊTRE': 'probably',
        'PROBABLEMENT PAS': 'probably_not'
    }

    def __init__(self, catalog_service: CatalogService):
        self.catalog_service = catalog_service

    def start_new_game(self, catalog_db: List[Dict]) -> AkinetixGameState:
        """Initialise une nouvelle partie et retourne l'état initial."""
        logger.info("Starting new Akinetix game session.")
        fine_attrs = self.catalog_service.get_akinetix_attributes()
        engine = ClassicalAkinetixService(catalog_db, fine_attributes=fine_attrs)
        next_attr = engine.propose_next_question()
        
        return AkinetixGameState(
            history=[],
            current_q=engine.format_question(next_attr),
            current_attr=next_attr,
            game_over=False,
            ai_guess=None,
            probs=engine.probs.tolist(),
            asked_attrs=list(engine.asked_attributes)
        )

    def process_answer(self, catalog_db: List[Dict], state: AkinetixGameState, raw_answer: str) -> AkinetixGameState:
        """
        Traite une réponse utilisateur, met à jour les probabilités
        et décide de la suite.
        """
        answer = self.ANSWER_MAPPING.get(raw_answer.upper(), 'dont_know')
        logger.debug(f"Processing answer: {raw_answer} -> {answer}")
        
        fine_attrs = self.catalog_service.get_akinetix_attributes()
        engine = ClassicalAkinetixService(
            catalog_db, 
            fine_attributes=fine_attrs,
            probs=state.probs,
            asked_attributes=state.asked_attrs
        )
        
        if state.current_attr:
            engine.update_probabilities(state.current_attr, answer)
        
        # Enregistrement dans l'historique
        state.history.append(AkinetixQuestion(q=state.current_q, a=raw_answer))
        
        best_title, best_prob = engine.get_best_guess()
        steps = len(engine.asked_attributes)
        
        # Mise à jour de l'état
        state.probs = engine.probs.tolist()
        state.asked_attrs = list(engine.asked_attributes)

        if (best_prob > self.PROBABILITY_THRESHOLD and steps >= self.MIN_STEPS_BEFORE_GUESS) or steps >= self.MAX_STEPS_TOTAL:
            logger.info(f"Game over reached. AI guess: {best_title} (prob: {best_prob:.2f})")
            state.current_q = f"Est-ce que tu penses à : {best_title} ?"
            state.ai_guess = best_title
            state.game_over = True
        else:
            next_attr = engine.propose_next_question()
            if next_attr:
                state.current_q = engine.format_question(next_attr)
                state.current_attr = next_attr
            else:
                logger.warning("No more questions available. Forcing guess.")
                state.current_q = f"Je ne sais plus quoi demander... Serait-ce {best_title} ?"
                state.ai_guess = best_title
                state.game_over = True
            
        return state

    def get_state(self, port: GameStatePort) -> AkinetixGameState:
        """Charge l'état spécifique à Akinetix depuis le port."""
        history_raw = port.get('akinetix_history', [])
        history = [AkinetixQuestion(**q) if isinstance(q, dict) else q for q in history_raw]
        
        return AkinetixGameState(
            history=history,
            current_q=port.get('akinetix_current_q'),
            current_attr=port.get('akinetix_current_attr'),
            game_over=port.get('akinetix_game_over', False),
            ai_guess=port.get('akinetix_ai_guess'),
            probs=port.get('akinetix_probs', []),
            asked_attrs=port.get('akinetix_asked_attrs', []),
            is_daily=port.get('is_daily', False)
        )

    def save_state(self, port: GameStatePort, state: AkinetixGameState) -> None:
        """Sauvegarde l'état spécifique à Akinetix dans le port."""
        port.update({
            'akinetix_history': [q.model_dump() for q in state.history],
            'akinetix_current_q': state.current_q,
            'akinetix_current_attr': state.current_attr,
            'akinetix_game_over': state.game_over,
            'akinetix_ai_guess': state.ai_guess,
            'akinetix_probs': state.probs,
            'akinetix_asked_attrs': state.asked_attrs,
            'is_daily': state.is_daily
        })
    
    def reset_state(self, port: GameStatePort) -> None:
        """Réinitialise l'état Akinetix dans le port."""
        port.update({
            'akinetix_history': [],
            'akinetix_current_q': None,
            'akinetix_current_attr': None,
            'akinetix_game_over': False,
            'akinetix_ai_guess': None,
            'akinetix_probs': [],
            'akinetix_asked_attrs': [],
            'is_daily': False
        })
