from animetix.models import Profile
from core.domain.entities.user import UserProfile


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
            ranked_max_points=django_profile.ranked_max_points,
            tier=django_profile.tier,
            api_key=django_profile.api_key_hash,
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
        django_profile.tier = domain_profile.tier

        # If the domain api_key is different from current hash, it's likely a new raw key
        if (
            domain_profile.api_key
            and domain_profile.api_key != django_profile.api_key_hash
        ):
            django_profile.set_api_key(domain_profile.api_key)

        django_profile.save()
