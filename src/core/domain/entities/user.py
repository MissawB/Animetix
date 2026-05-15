from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class UserProfile:
    id: int
    username: str
    xp: int = 0
    current_streak: int = 0
    max_streak: int = 0
    last_win_date: Optional[date] = None
    total_wins: int = 0
    total_games: int = 0
    ranked_points: int = 0
    ranked_max_points: int = 0

    @property
    def rank_label(self) -> str:
        if self.ranked_points < 500: return "Bronze 🥉"
        if self.ranked_points < 1500: return "Argent 🥈"
        if self.ranked_points < 3000: return "Or 🥇"
        if self.ranked_points < 6000: return "Platine 💎"
        if self.ranked_points < 10000: return "Diamant 💠"
        return "Maître de la Data 👑"
