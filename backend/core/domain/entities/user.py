from dataclasses import dataclass
from datetime import date
from typing import Optional


def rank_label_for(ranked_points: int) -> str:
    """Canonical ranked-ladder label for a ranked-points total.

    Shared by the domain entity and the Django ``Profile.rank`` property so
    the ladder thresholds live in exactly one place.
    """
    if ranked_points < 500:
        return "Bronze 🥉"
    if ranked_points < 1500:
        return "Argent 🥈"
    if ranked_points < 3000:
        return "Or 🥇"
    if ranked_points < 6000:
        return "Platine 💎"
    if ranked_points < 10000:
        return "Diamant 💠"
    return "Maître de la Data 👑"


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
    tier: str = "free"
    api_key: Optional[str] = (
        None  # Stores the raw key on creation, or hash when loaded from DB
    )

    @property
    def rank_label(self) -> str:
        return rank_label_for(self.ranked_points)
