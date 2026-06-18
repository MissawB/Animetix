from datetime import date, timedelta

import pytest
from core.domain.entities.user import UserProfile
from core.domain.services.ranking_service import RankingService


@pytest.fixture
def ranking_service():
    return RankingService()


def test_calculate_win_normal(ranking_service):
    profile = UserProfile(id=1, username="test", xp=0)
    updated = ranking_service.calculate_win(profile)

    assert updated.total_wins == 1
    assert updated.xp == 50
    assert updated.current_streak == 1
    assert updated.last_win_date == date.today()


def test_calculate_win_daily(ranking_service):
    profile = UserProfile(id=1, username="test", xp=0)
    updated = ranking_service.calculate_win(profile, is_daily=True)
    assert updated.xp == 150


def test_calculate_win_ranked(ranking_service):
    profile = UserProfile(id=1, username="test", xp=0, ranked_points=0)
    updated = ranking_service.calculate_win(profile, is_ranked=True, item_rank=100)
    # Point gain = max(10, 100/5) = 20
    assert updated.ranked_points == 20
    # XP gain = 20 * 2 = 40
    assert updated.xp == 40
    assert updated.ranked_max_points == 20


def test_streak_increment(ranking_service):
    yesterday = date.today() - timedelta(days=1)
    profile = UserProfile(
        id=1, username="test", xp=0, current_streak=1, last_win_date=yesterday
    )

    updated = ranking_service.calculate_win(profile)
    assert updated.current_streak == 2
    assert updated.max_streak == 2


def test_streak_reset(ranking_service):
    two_days_ago = date.today() - timedelta(days=2)
    profile = UserProfile(
        id=1, username="test", xp=0, current_streak=5, last_win_date=two_days_ago
    )

    updated = ranking_service.calculate_win(profile)
    assert updated.current_streak == 1
