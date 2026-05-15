from typing import Dict
from core.domain.entities.user import UserProfile
from animetix.models import Profile

class DjangoProfileAdapter:
    @staticmethod
    def to_domain(django_profile: Profile) -> UserProfile:
        return UserProfile(
            id=django_profile.user.id,
            username=django_profile.user.username,
            xp=django_profile.xp,
            current_streak=django_profile.current_streak,
            max_streak=django_profile.max_streak,
            last_win_date=django_profile.last_win_date,
            total_wins=django_profile.total_wins,
            total_games=django_profile.total_games,
            ranked_points=django_profile.ranked_points,
            ranked_max_points=django_profile.ranked_max_points
        )

    @staticmethod
    def update_django(django_profile: Profile, domain_profile: UserProfile):
        django_profile.xp = domain_profile.xp
        django_profile.current_streak = domain_profile.current_streak
        django_profile.max_streak = domain_profile.max_streak
        django_profile.last_win_date = domain_profile.last_win_date
        django_profile.total_wins = domain_profile.total_wins
        django_profile.total_games = domain_profile.total_games
        django_profile.ranked_points = domain_profile.ranked_points
        django_profile.ranked_max_points = domain_profile.ranked_max_points
        django_profile.save()
