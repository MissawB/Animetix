from abc import ABC, abstractmethod
from typing import List, Optional
from ..domain.entities.achievement import AchievementDefinition, GameEvent

class AchievementPort(ABC):
    @abstractmethod
    def get_all_achievements(self) -> List[AchievementDefinition]:
        """Récupère toutes les définitions de succès."""
        pass

    @abstractmethod
    def get_user_unlocked_codes(self, user_id: int) -> List[str]:
        """Récupère les codes des succès déjà débloqués par l'utilisateur."""
        pass

    @abstractmethod
    def unlock_achievement(self, user_id: int, achievement_code: str):
        """Enregistre le déblocage d'un succès pour un utilisateur."""
        pass
