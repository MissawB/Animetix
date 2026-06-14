from abc import ABC, abstractmethod
from typing import List, Optional
from ..domain.entities.achievement import AchievementDefinition

class AchievementPort(ABC):
    """
    Port définissant les interactions avec la persistence des succès (achievements).
    """

    @abstractmethod
    def get_all_achievements(self) -> List[AchievementDefinition]:
        """
        Récupère toutes les définitions de succès disponibles dans le système.
        
        Returns:
            List[AchievementDefinition]: La liste des définitions de succès.
        """
        pass

    @abstractmethod
    def get_user_unlocked_codes(self, user_id: int) -> List[str]:
        """
        Récupère les codes uniques des succès déjà débloqués par un utilisateur.
        
        Args:
            user_id (int): L'ID de l'utilisateur.
            
        Returns:
            List[str]: Liste des codes de succès débloqués.
        """
        pass

    @abstractmethod
    def unlock_achievement(self, user_id: int, achievement_code: str) -> None:
        """
        Enregistre le déblocage d'un succès pour un utilisateur et attribue les récompenses.
        
        Args:
            user_id (int): L'ID de l'utilisateur.
            achievement_code (str): Le code unique du succès à débloquer.
        """
        pass
