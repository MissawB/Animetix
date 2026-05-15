from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class GameEvent:
    user_id: int
    game_mode: str
    media_type: str
    was_won: bool
    is_daily: bool = False
    is_ranked: bool = False
    attempts: int = 0
    time_taken: float = 0.0
    streak: int = 0
    total_wins: int = 0
    total_games: int = 0
    item_rarity: str = "Common"

@dataclass
class AchievementDefinition:
    code: str
    name: str
    description: str
    icon: str
    xp_reward: int
    rarity: str = "Common"
