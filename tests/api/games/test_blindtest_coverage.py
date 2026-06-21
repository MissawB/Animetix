"""Coverage tests for animetix.api.games.blindtest.

Exercises the Blindtest endpoints (state / start / guess) against the real
Django session. The DI ``catalog_service`` / ``blind_test_service`` /
``game_service`` providers are mocked via instance-level container overrides.

``blind_test_service`` is a mock; ``get_state`` returns a controllable
``SimpleNamespace`` standing in for the Blindtest state object.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from animetix.containers import container
from dependency_injector import providers
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def mock_catalog():
    return {
        "title_to_full_data": {
            "Naruto": {"image": "http://naruto.jpg"},
            "Bleach": {"image": "http://bleach.jpg"},
        }
    }


def _state(**kwargs):
    defaults = dict(
        secret=None,
        video=None,
        type=None,
        song=None,
        artists=None,
        guesses=[],
        game_over=False,
        is_daily=False,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


_THEME = {
    "anime_title": "Naruto",
    "video_url": "http://video.mp4",
    "type": "opening",
    "song_title": "Blue Bird",
    "artists": ["Ikimono"],
}


# --------------------------------------------------------------------------- #
# BlindtestGameStateView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_state_no_game(api_client):
    bt = MagicMock()
    bt.get_state.return_value = _state(secret=None)
    with container.core.blind_test_service.override(providers.Object(bt)):
        resp = api_client.get(reverse("api_blindtest_state"))
    assert resp.status_code == 400
    assert resp.json()["error"] == "No game in progress"


@pytest.mark.django_db
def test_state_in_progress_hides_secret(api_client):
    bt = MagicMock()
    bt.get_state.return_value = _state(
        secret="Naruto",
        video="http://video.mp4",
        type="opening",
        song="Blue Bird",
        artists=["Ikimono"],
        game_over=False,
    )
    with container.core.blind_test_service.override(providers.Object(bt)):
        resp = api_client.get(reverse("api_blindtest_state"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["video_url"] == "http://video.mp4"
    assert data["blindtest_song"] == "Blue Bird"
    assert data["secret_title"] is None  # hidden while running


@pytest.mark.django_db
def test_state_game_over_reveals_secret(api_client):
    bt = MagicMock()
    bt.get_state.return_value = _state(secret="Naruto", game_over=True)
    with container.core.blind_test_service.override(providers.Object(bt)):
        resp = api_client.get(reverse("api_blindtest_state"))
    assert resp.status_code == 200
    assert resp.json()["secret_title"] == "Naruto"


# --------------------------------------------------------------------------- #
# BlindtestGameStartView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_start_catalog_not_found(api_client):
    cat = MagicMock()
    cat.load_data.return_value = None
    bt = MagicMock()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.blind_test_service.override(providers.Object(bt)),
    ):
        resp = api_client.post(reverse("api_blindtest_start"), {}, format="json")
    assert resp.status_code == 404
    assert resp.json()["error"] == "Catalog not found"


@pytest.mark.django_db
def test_start_no_theme(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    bt = MagicMock()
    bt.get_random_theme.return_value = None
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.blind_test_service.override(providers.Object(bt)),
    ):
        resp = api_client.post(reverse("api_blindtest_start"), {}, format="json")
    assert resp.status_code == 500
    assert resp.json()["error"] == "Failed to select theme"


@pytest.mark.django_db
def test_start_random_success(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    bt = MagicMock()
    bt.get_random_theme.return_value = _THEME
    bt.get_state.return_value = _state()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.blind_test_service.override(providers.Object(bt)),
    ):
        resp = api_client.post(
            reverse("api_blindtest_start"), {"type": "opening"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["video_url"] == "http://video.mp4"
    assert data["theme_type"] == "opening"
    assert data["game_over"] is False
    bt.get_random_theme.assert_called_once_with(theme_type="opening")
    bt.save_state.assert_called_once()


@pytest.mark.django_db
def test_start_daily_success(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    bt = MagicMock()
    bt.get_daily_theme.return_value = _THEME
    bt.get_state.return_value = _state()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.blind_test_service.override(providers.Object(bt)),
    ):
        resp = api_client.post(
            reverse("api_blindtest_start"), {"is_daily": True}, format="json"
        )
    assert resp.status_code == 200
    assert resp.json()["is_daily"] is True
    bt.get_daily_theme.assert_called_once()
    bt.get_random_theme.assert_not_called()


# --------------------------------------------------------------------------- #
# BlindtestGameGuessView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_guess_no_game(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    bt = MagicMock()
    bt.get_state.return_value = _state(secret=None)
    game = MagicMock()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.blind_test_service.override(providers.Object(bt)),
        container.core.game_service.override(providers.Object(game)),
    ):
        resp = api_client.post(
            reverse("api_blindtest_guess"), {"guess": "Naruto"}, format="json"
        )
    assert resp.status_code == 400
    assert resp.json()["error"] == "No game in progress"


@pytest.mark.django_db
def test_guess_already_over(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    bt = MagicMock()
    bt.get_state.return_value = _state(secret="Naruto", game_over=True)
    game = MagicMock()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.blind_test_service.override(providers.Object(bt)),
        container.core.game_service.override(providers.Object(game)),
    ):
        resp = api_client.post(
            reverse("api_blindtest_guess"), {"guess": "Naruto"}, format="json"
        )
    assert resp.status_code == 400
    assert resp.json()["error"] == "Game already over"


@pytest.mark.django_db
def test_guess_missing_guess(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    bt = MagicMock()
    bt.get_state.return_value = _state(secret="Naruto")
    game = MagicMock()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.blind_test_service.override(providers.Object(bt)),
        container.core.game_service.override(providers.Object(game)),
    ):
        resp = api_client.post(reverse("api_blindtest_guess"), {}, format="json")
    assert resp.status_code == 400
    assert resp.json()["error"] == "Guess is required"


@pytest.mark.django_db
def test_guess_incorrect(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    bt = MagicMock()
    bt.get_state.return_value = _state(secret="Naruto", guesses=[])
    game = MagicMock()
    game.check_title_match.return_value = False
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.blind_test_service.override(providers.Object(bt)),
        container.core.game_service.override(providers.Object(game)),
    ):
        resp = api_client.post(
            reverse("api_blindtest_guess"), {"guess": "Bleach"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is False
    assert data["game_over"] is False
    assert data["guesses"][0]["title"] == "Bleach"
    assert data["guesses"][0]["image"] == "http://bleach.jpg"


@pytest.mark.django_db
def test_guess_unknown_title_image_none(api_client, mock_catalog):
    """A guess not present in the catalog -> image None, still scored."""
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    bt = MagicMock()
    bt.get_state.return_value = _state(secret="Naruto", guesses=[])
    game = MagicMock()
    game.check_title_match.return_value = False
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.blind_test_service.override(providers.Object(bt)),
        container.core.game_service.override(providers.Object(game)),
    ):
        resp = api_client.post(
            reverse("api_blindtest_guess"), {"guess": "Unknown"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["guesses"][0]["title"] == "Unknown"
    assert data["guesses"][0]["image"] is None


@pytest.mark.django_db
def test_guess_correct_authenticated_creates_session(api_client, mock_catalog):
    from animetix.models import GameplaySession

    user = User.objects.create_user("btwin", password="x")
    api_client.force_authenticate(user=user)
    ach = MagicMock()
    ach.name = "BT Win"
    ach.description = "d"
    ach.xp_reward = 5
    ach.badge_url = "http://b.png"
    user.profile.add_win = MagicMock(return_value=[ach])

    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    bt = MagicMock()
    bt.get_state.return_value = _state(secret="Naruto", guesses=[])
    game = MagicMock()
    game.check_title_match.return_value = True
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.blind_test_service.override(providers.Object(bt)),
        container.core.game_service.override(providers.Object(game)),
    ):
        resp = api_client.post(
            reverse("api_blindtest_guess"), {"guess": "Naruto"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is True
    assert data["game_over"] is True
    assert data["secret_title"] == "Naruto"
    assert data["newly_unlocked_achievements"][0]["name"] == "BT Win"
    assert GameplaySession.objects.filter(target_item="Naruto", was_won=True).exists()


@pytest.mark.django_db
def test_guess_correct_add_win_raises_is_handled(api_client, mock_catalog):
    from animetix.models import GameplaySession

    user = User.objects.create_user("btwinerr", password="x")
    api_client.force_authenticate(user=user)
    user.profile.add_win = MagicMock(side_effect=RuntimeError("boom"))

    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    bt = MagicMock()
    bt.get_state.return_value = _state(secret="Naruto", guesses=[])
    game = MagicMock()
    game.check_title_match.return_value = True
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.blind_test_service.override(providers.Object(bt)),
        container.core.game_service.override(providers.Object(game)),
    ):
        resp = api_client.post(
            reverse("api_blindtest_guess"), {"guess": "Naruto"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is True
    assert data["newly_unlocked_achievements"] == []
    assert GameplaySession.objects.filter(target_item="Naruto", was_won=True).exists()
