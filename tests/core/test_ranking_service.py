from datetime import date, timedelta
from unittest.mock import patch

import pytest
from core.domain.entities.user import UserProfile
from core.domain.services.ranking_service import RankingService

# All tests pin date.today() via freezegun-style patching to avoid midnight flakes.
FIXED_TODAY = date(2026, 6, 15)


@pytest.fixture
def ranking_service():
    return RankingService()


@patch("core.domain.services.ranking_service.date")
def test_calculate_win_normal(mock_date, ranking_service):
    mock_date.today.return_value = FIXED_TODAY
    mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

    profile = UserProfile(id=1, username="test", xp=0)
    updated = ranking_service.calculate_win(profile)

    assert updated.total_wins == 1
    assert updated.xp == 50
    assert updated.current_streak == 1
    assert updated.last_win_date == FIXED_TODAY


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


@patch("core.domain.services.ranking_service.date")
def test_streak_increment(mock_date, ranking_service):
    mock_date.today.return_value = FIXED_TODAY
    mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

    yesterday = FIXED_TODAY - timedelta(days=1)
    profile = UserProfile(
        id=1, username="test", xp=0, current_streak=1, last_win_date=yesterday
    )

    updated = ranking_service.calculate_win(profile)
    assert updated.current_streak == 2
    assert updated.max_streak == 2


@patch("core.domain.services.ranking_service.date")
def test_streak_reset(mock_date, ranking_service):
    mock_date.today.return_value = FIXED_TODAY
    mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

    two_days_ago = FIXED_TODAY - timedelta(days=2)
    profile = UserProfile(
        id=1, username="test", xp=0, current_streak=5, last_win_date=two_days_ago
    )

    updated = ranking_service.calculate_win(profile)
    assert updated.current_streak == 1
