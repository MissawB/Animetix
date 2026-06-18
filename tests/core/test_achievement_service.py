import pytest
from unittest.mock import MagicMock
from core.domain.services.achievement_service import (
    AchievementDomainService,
    GameEventListener,
)
from core.domain.entities.achievement import AchievementDefinition, GameEvent


@pytest.fixture
def mock_port():
    return MagicMock()


@pytest.fixture
def achievement_service(mock_port):
    return AchievementDomainService(port=mock_port)


def test_no_win_no_achievement(achievement_service):
    event = GameEvent(user_id=1, was_won=False, game_mode="classic", media_type="Anime")
    assert achievement_service.check_and_unlock(event) == []


def test_unlock_first_win(achievement_service, mock_port):
    ach = AchievementDefinition(
        code="first_win", name="First Win", description="...", icon="🏆", xp_reward=100
    )
    mock_port.get_all_achievements.return_value = [ach]
    mock_port.get_user_unlocked_codes.return_value = []

    event = GameEvent(user_id=1, was_won=True, game_mode="classic", media_type="Anime")
    unlocked = achievement_service.check_and_unlock(event)

    assert len(unlocked) == 1
    assert unlocked[0].code == "first_win"
    mock_port.unlock_achievement.assert_called_with(1, "first_win")


def test_streak_achievements(achievement_service, mock_port):
    ach3 = AchievementDefinition(
        code="streak_3", name="Streak 3", description="...", icon="🔥", xp_reward=300
    )
    mock_port.get_all_achievements.return_value = [ach3]
    mock_port.get_user_unlocked_codes.return_value = []

    # Event with streak 3
    event = GameEvent(
        user_id=1, was_won=True, streak=3, game_mode="classic", media_type="Anime"
    )
    unlocked = achievement_service.check_and_unlock(event)
    assert "streak_3" in [a.code for a in unlocked]


def test_volume_achievements(achievement_service, mock_port):
    ach10 = AchievementDefinition(
        code="wins_10", name="10 Wins", description="...", icon="⭐", xp_reward=500
    )
    mock_port.get_all_achievements.return_value = [ach10]
    mock_port.get_user_unlocked_codes.return_value = []

    event = GameEvent(
        user_id=1, was_won=True, total_wins=10, game_mode="classic", media_type="Anime"
    )
    unlocked = achievement_service.check_and_unlock(event)
    assert "wins_10" in [a.code for a in unlocked]


def test_mode_specific_achievements(achievement_service, mock_port):
    ach_daily = AchievementDefinition(
        code="daily_master",
        name="Daily Master",
        description="...",
        icon="📅",
        xp_reward=200,
    )
    mock_port.get_all_achievements.return_value = [ach_daily]
    mock_port.get_user_unlocked_codes.return_value = []

    event = GameEvent(
        user_id=1, was_won=True, is_daily=True, game_mode="classic", media_type="Anime"
    )
    unlocked = achievement_service.check_and_unlock(event)
    assert "daily_master" in [a.code for a in unlocked]


def test_speed_demon(achievement_service, mock_port):
    ach_speed = AchievementDefinition(
        code="speed_demon",
        name="Speed Demon",
        description="...",
        icon="⚡",
        xp_reward=400,
    )
    mock_port.get_all_achievements.return_value = [ach_speed]
    mock_port.get_user_unlocked_codes.return_value = []

    event = GameEvent(
        user_id=1, was_won=True, attempts=3, game_mode="classic", media_type="Anime"
    )
    unlocked = achievement_service.check_and_unlock(event)
    assert "speed_demon" in [a.code for a in unlocked]


def test_rarity_achievements(achievement_service, mock_port):
    ach_rare = AchievementDefinition(
        code="rare_finder",
        name="Rare Finder",
        description="...",
        icon="💎",
        xp_reward=300,
    )
    mock_port.get_all_achievements.return_value = [ach_rare]
    mock_port.get_user_unlocked_codes.return_value = []

    event = GameEvent(
        user_id=1,
        was_won=True,
        item_rarity="Rare",
        game_mode="classic",
        media_type="Anime",
    )
    unlocked = achievement_service.check_and_unlock(event)
    assert "rare_finder" in [a.code for a in unlocked]


def test_game_event_listener(achievement_service):
    listener = GameEventListener(achievement_service)
    event = GameEvent(user_id=1, was_won=False, game_mode="classic", media_type="Anime")
    assert listener.on_game_finished(event) == []
