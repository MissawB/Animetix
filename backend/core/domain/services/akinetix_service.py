import logging
from typing import List, Dict, Optional, Any
from .akinetix_engine import AkinetixEngine
from .catalog_service import CatalogService
from core.ports.game_state_port import GameStatePort
from ..entities.akinetix import AkinetixGameState, AkinetixQuestion

logger = logging.getLogger('animetix.akinetix')

class AkinetixDomainService:
    """
    Service de domaine orchestrant le jeu Akinetix.
    Utilise désormais AkinetixEngine pour la logique algorithmique.
    """
    
    def __init__(self, catalog_service: CatalogService, engine: Optional[AkinetixEngine] = None):
        self.catalog_service = catalog_service
        self.engine = engine or AkinetixEngine(catalog_service)

    def start_new_game(self, catalog_db: List[Dict], mode: str = "classical") -> AkinetixGameState:
        """Initialise une nouvelle partie et retourne l'état initial."""
        return self.engine.start_game(catalog_db, mode=mode)

    def process_answer(self, catalog_db: List[Dict], state: AkinetixGameState, raw_answer: str, mode: str = "classical") -> AkinetixGameState:
        """
        Traite une réponse utilisateur, met à jour l'état et décide de la suite.
        """
        return self.engine.process_answer(catalog_db, state, raw_answer, mode=mode)

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
            user_target_id=port.get('akinetix_user_target_id'),
            user_target_name=port.get('akinetix_user_target_name'),
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
            'akinetix_user_target_id': state.user_target_id,
            'akinetix_user_target_name': state.user_target_name,
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
            'akinetix_user_target_id': None,
            'akinetix_user_target_name': None,
            'akinetix_probs': [],
            'akinetix_asked_attrs': [],
            'is_daily': False
        })
