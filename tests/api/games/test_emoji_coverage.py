"""Coverage tests for animetix.api.games.emoji.

Exercises the Emoji mode endpoints (state / start / guess) against the real
Django session (the session-state port reads/writes request.session). The DI
``catalog_service`` / ``emoji_service`` / ``game_service`` providers are mocked
via the dependency_injector container (instance-level override).
"""

from unittest.mock import MagicMock

import pytest
from animetix.containers import container
from dependency_injector import providers
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def _wire_container():
    # In this worktree the app-ready wiring leaves the @inject markers bound to
    # providers whose `persistence` sub-container link is stale, so resolving a real
    # service raises `Container.core.persistence.feedback_adapter is not defined`.
    # Re-wiring the view module rebinds the markers to the live instance providers so
    # that instance-level overrides take effect.
    #
    # IMPORTANT: we deliberately do NOT call ``container.reset_override()`` here.
    # On this dependency_injector version that call detaches the ``core`` ->
    # ``persistence`` DependenciesContainer link and re-triggers the bug. Each test
    # therefore scopes its overrides with a ``with`` block, which cleans itself up.
    import animetix.api.games.emoji as emoji_mod

    container.wire(modules=[emoji_mod])
    yield


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def mock_catalog():
    return {
        "title_to_full_data": {
            "Naruto": {
                "title": "Naruto",
                "title_english": "Naruto EN",
                "title_native": "ナルト",
                "image": "http://img.jpg",
                "description": "Ninja anime",
            },
            "Bleach": {
                "title": "Bleach",
                "title_english": "Bleach EN",
                "title_native": "ブリーチ",
                "image": "http://img2.jpg",
                "description": "Soul reaper",
            },
        },
        "title_to_index": {"Naruto": 1, "Bleach": 2},
        "lookup": [{"title": "Naruto"}, {"title": "Bleach"}],
    }


# --------------------------------------------------------------------------- #
# EmojiGameStateView (auto-start)
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_state_auto_start_success(api_client, mock_catalog):
    """Empty session -> view auto-starts a game and returns emojis."""
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    emoji = MagicMock()
    emoji.select_secret.return_value = "Naruto"
    emoji.generate_emojis.return_value = ["🍥", "🦊"]

    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.emoji_service.override(providers.Object(emoji)),
    ):
        resp = api_client.get(reverse("api_emoji_state"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["emojis"] == ["🍥", "🦊"]
    assert data["game_over"] is False
    assert data["secret_title"] is None  # hidden while game running


@pytest.mark.django_db
def test_state_auto_start_fallback_media_type(api_client, mock_catalog):
    """First media_type empty -> falls back through Anime/Manga/Character."""
    cat = MagicMock()
    # Anime -> None, Manga -> catalog
    cat.load_data.side_effect = [None, None, mock_catalog]
    emoji = MagicMock()
    emoji.select_secret.return_value = "Bleach"
    emoji.generate_emojis.return_value = ["💀"]

    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.emoji_service.override(providers.Object(emoji)),
    ):
        resp = api_client.get(reverse("api_emoji_state"))
    assert resp.status_code == 200
    assert resp.json()["emojis"] == ["💀"]


@pytest.mark.django_db
def test_state_auto_start_fails_no_catalog(api_client):
    """No catalog for any media_type -> 400 auto-start failed."""
    cat = MagicMock()
    cat.load_data.return_value = None
    emoji = MagicMock()

    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.emoji_service.override(providers.Object(emoji)),
    ):
        resp = api_client.get(reverse("api_emoji_state"))
    assert resp.status_code == 400
    assert "auto-start failed" in resp.json()["error"]


# --------------------------------------------------------------------------- #
# EmojiGameStartView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_start_catalog_not_found(api_client):
    cat = MagicMock()
    cat.load_data.return_value = None
    emoji = MagicMock()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.emoji_service.override(providers.Object(emoji)),
    ):
        resp = api_client.post(
            reverse("api_emoji_start"), {"media_type": "Anime"}, format="json"
        )
    assert resp.status_code == 404
    assert resp.json()["error"] == "Catalog not found"


@pytest.mark.django_db
def test_start_success(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    emoji = MagicMock()
    emoji.select_secret.return_value = "Naruto"
    emoji.generate_emojis.return_value = ["🍥", "🦊"]
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.emoji_service.override(providers.Object(emoji)),
    ):
        resp = api_client.post(
            reverse("api_emoji_start"), {"media_type": "Anime"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "started"
    assert data["emojis"] == ["🍥", "🦊"]
    emoji.select_secret.assert_called_once()


@pytest.mark.django_db
def test_start_select_secret_failure(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    emoji = MagicMock()
    emoji.select_secret.return_value = None
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.emoji_service.override(providers.Object(emoji)),
    ):
        resp = api_client.post(
            reverse("api_emoji_start"), {"media_type": "Anime"}, format="json"
        )
    assert resp.status_code == 500
    assert resp.json()["error"] == "Failed to select secret title"


# --------------------------------------------------------------------------- #
# EmojiGameGuessView
# --------------------------------------------------------------------------- #
def _start_game(api_client, cat, emoji, secret="Naruto"):
    emoji.select_secret.return_value = secret
    emoji.generate_emojis.return_value = ["🍥"]
    return api_client.post(
        reverse("api_emoji_start"), {"media_type": "Anime"}, format="json"
    )


@pytest.mark.django_db
def test_guess_no_game(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    game = MagicMock()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.game_service.override(providers.Object(game)),
    ):
        resp = api_client.post(
            reverse("api_emoji_guess"), {"guess": "Naruto"}, format="json"
        )
    assert resp.status_code == 400
    assert resp.json()["error"] == "No game in progress"


@pytest.mark.django_db
def test_guess_missing_guess_field(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    emoji = MagicMock()
    game = MagicMock()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.emoji_service.override(providers.Object(emoji)),
        container.core.game_service.override(providers.Object(game)),
    ):
        _start_game(api_client, cat, emoji)
        resp = api_client.post(reverse("api_emoji_guess"), {}, format="json")
    assert resp.status_code == 400
    assert resp.json()["error"] == "Guess is required"


@pytest.mark.django_db
def test_guess_title_not_in_catalog(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    emoji = MagicMock()
    game = MagicMock()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.emoji_service.override(providers.Object(emoji)),
        container.core.game_service.override(providers.Object(game)),
    ):
        _start_game(api_client, cat, emoji)
        resp = api_client.post(
            reverse("api_emoji_guess"), {"guess": "Unknown"}, format="json"
        )
    assert resp.status_code == 400
    assert "not in catalog" in resp.json()["error"]


@pytest.mark.django_db
def test_guess_incorrect_keeps_game_running(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    emoji = MagicMock()
    game = MagicMock()
    game.check_title_match.return_value = False
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.emoji_service.override(providers.Object(emoji)),
        container.core.game_service.override(providers.Object(game)),
    ):
        _start_game(api_client, cat, emoji)
        resp = api_client.post(
            reverse("api_emoji_guess"), {"guess": "Bleach"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is False
    assert data["game_over"] is False
    assert data["guess_count"] == 1
    assert data["latest_guess"]["title"] == "Bleach"


@pytest.mark.django_db
def test_guess_correct_authenticated_creates_session(api_client, mock_catalog):
    from animetix.models import GameplaySession

    user = User.objects.create_user("emojiwinner", password="x")
    api_client.force_authenticate(user=user)
    ach = MagicMock()
    ach.name = "Win"
    ach.description = "desc"
    ach.xp_reward = 10
    ach.badge_url = "http://b.png"
    user.profile.add_win = MagicMock(return_value=[ach])

    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    emoji = MagicMock()
    game = MagicMock()
    game.check_title_match.return_value = True
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.emoji_service.override(providers.Object(emoji)),
        container.core.game_service.override(providers.Object(game)),
    ):
        _start_game(api_client, cat, emoji, secret="Naruto")
        resp = api_client.post(
            reverse("api_emoji_guess"), {"guess": "Naruto"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is True
    assert data["game_over"] is True
    assert data["secret_title"] == "Naruto"
    assert data["newly_unlocked_achievements"][0]["name"] == "Win"
    assert GameplaySession.objects.filter(target_item="Naruto", was_won=True).exists()


@pytest.mark.django_db
def test_guess_when_game_over(api_client, mock_catalog):
    user = User.objects.create_user("emojiover", password="x")
    api_client.force_authenticate(user=user)
    user.profile.add_win = MagicMock(return_value=[])

    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    emoji = MagicMock()
    game = MagicMock()
    game.check_title_match.return_value = True
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.emoji_service.override(providers.Object(emoji)),
        container.core.game_service.override(providers.Object(game)),
    ):
        _start_game(api_client, cat, emoji, secret="Naruto")
        api_client.post(reverse("api_emoji_guess"), {"guess": "Naruto"}, format="json")
        resp = api_client.post(
            reverse("api_emoji_guess"), {"guess": "Naruto"}, format="json"
        )
    assert resp.status_code == 400
    assert resp.json()["error"] == "Game already over"
