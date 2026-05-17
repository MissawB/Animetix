from typing import List, Optional
from ..entities.achievement import AchievementDefinition, GameEvent
from ...ports.achievement_port import AchievementPort

class AchievementDomainService:
    def __init__(self, port: AchievementPort):
        self.port = port

    def check_and_unlock(self, event: GameEvent) -> List[AchievementDefinition]:
        """
        Vérifie si l'événement de jeu débloque de nouveaux succès.
        Retourne la liste des succès nouvellement débloqués.
        """
        if not event.was_won:
            return []

        unlocked_codes = self.port.get_user_unlocked_codes(event.user_id)
        all_definitions = self.port.get_all_achievements()
        
        newly_unlocked = []
        
        for ach in all_definitions:
            if ach.code in unlocked_codes:
                continue
            
            should_unlock = False
            
            # --- RÈGLES DE DÉBLOCAGE ---
            
            # Succès de Bienvenue
            if ach.code == 'first_win':
                should_unlock = True
                
            # Succès de Streak
            elif ach.code == 'streak_3' and event.streak >= 3:
                should_unlock = True
            elif ach.code == 'streak_7' and event.streak >= 7:
                should_unlock = True
            elif ach.code == 'streak_10' and event.streak >= 10:
                should_unlock = True
                
            # Succès de Volume (Total Wins)
            elif ach.code == 'wins_10' and event.total_wins >= 10:
                should_unlock = True
            elif ach.code == 'wins_50' and event.total_wins >= 50:
                should_unlock = True
            elif ach.code == 'wins_100' and event.total_wins >= 100:
                should_unlock = True
                
            # Succès Spécifiques aux Modes
            elif ach.code == 'daily_master' and event.is_daily:
                should_unlock = True
            elif ach.code == 'ranked_warrior' and event.is_ranked:
                should_unlock = True
                
            # Succès de Rapidité
            elif ach.code == 'speed_demon' and event.attempts <= 3 and event.game_mode == 'classic':
                should_unlock = True
            
            # Succès de Rareté
            elif ach.code == 'rare_finder' and event.item_rarity in ['Rare', 'Epic', 'Legendary']:
                should_unlock = True
            elif ach.code == 'legendary_hunter' and event.item_rarity == 'Legendary':
                should_unlock = True

            if should_unlock:
                self.port.unlock_achievement(event.user_id, ach.code)
                newly_unlocked.append(ach)
                
        return newly_unlocked

    def unlock_by_code(self, user_id: int, achievement_code: str):
        """Force le déblocage d'un succès spécifique."""
        unlocked_codes = self.port.get_user_unlocked_codes(user_id)
        if achievement_code not in unlocked_codes:
            self.port.unlock_achievement(user_id, achievement_code)

class GameEventListener:
    """
    Écouteur d'événements de jeu qui déclenche les vérifications de succès.
    """
    def __init__(self, achievement_service: AchievementDomainService):
        self.achievement_service = achievement_service

    def on_game_finished(self, event: GameEvent) -> List[AchievementDefinition]:
        return self.achievement_service.check_and_unlock(event)
