from datetime import date, timedelta
from ..entities.user import UserProfile

class RankingService:
    def calculate_win(self, profile: UserProfile, is_daily: bool = False, is_ranked: bool = False, item_rank: int = 100) -> UserProfile:
        profile.total_wins += 1
        profile.total_games += 1
        
        xp_gain: int = 50
        if is_daily: 
            xp_gain = 150
        
        if is_ranked:
            point_gain: int = max(10, int(item_rank / 5))
            profile.ranked_points += point_gain
            xp_gain = point_gain * 2
            if profile.ranked_points > profile.ranked_max_points:
                profile.ranked_max_points = profile.ranked_points
        
        profile.xp += xp_gain
        today: date = date.today()
        
        if profile.last_win_date == today - timedelta(days=1):
            profile.current_streak += 1
        elif profile.last_win_date != today:
            profile.current_streak = 1
            
        if profile.current_streak > profile.max_streak:
            profile.max_streak = profile.current_streak
            
        profile.last_win_date = today
        return profile
