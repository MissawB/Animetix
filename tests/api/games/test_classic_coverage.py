"""Coverage tests for backend/api/animetix/api/games/classic.py.

These exercise the Classic mode endpoints (state / start / guess / reveal)
against the real Django session (the session state port reads request.session),
overriding the DI catalog/game services via the dependency_injector container.
"""

from unittest.mock import MagicMock

import pytest
from animetix.containers import container
from dependency_injector import providers
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient

# NB: the per-test wiring guard lives in conftest.py (``_rewire_game_modules``).
# We never call ``container.reset_override()`` -- on this dependency_injector
# version it detaches the ``core -> persistence`` sub-container link and breaks the
# views. Each test scopes its overrides with ``with`` blocks, which self-clean.


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def mock_catalog():
    return {
        "title_to_full_data": {
            "Naruto": {
                "id": 1,
                "title": "Naruto",
                "description": "Ninja anime " * 30,
                "image": "http://img.jpg",
                "title_english": "Naruto EN",
                "title_native": "Naruto JP",
                "origin": "Japan",
                "year": 2002,
                "tags": ["action", "ninja", "shonen", "adventure", "battle", "extra"],
                "metadata": {"studio": "Pierrot"},
            },
            "One Piece": {
                "id": 2,
                "title": "One Piece",
                "description": "Pirate anime",
                "image": "http://img2.jpg",
            },
            "Bleach": {
                "id": 3,
                "title": "Bleach",
                "description": "Soul reaper anime",
                "image": "http://img3.jpg",
            },
        },
        "titles": ["Naruto", "One Piece", "Bleach"],
        "title_to_index": {"Naruto": 1, "One Piece": 2, "Bleach": 3},
        "lookup": [
            {"id": 1, "title": "Naruto"},
            {"id": 2, "title": "One Piece"},
            {"id": 3, "title": "Bleach"},
        ],
    }


def _override(catalog=None, game=None):
    """Return the list of container override context managers for the test."""
    overrides = []
    if catalog is not None:
        overrides.append(
            container.core.catalog_service.override(providers.Object(catalog))
        )
    if game is not None:
        overrides.append(container.core.game_service.override(providers.Object(game)))
    return overrides


# ---------------------------------------------------------------------------
# ClassicGameStateView
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_state_no_game_in_progress(api_client, mock_catalog):
    """GET state with empty session -> 400 No game in progress."""
    cat = MagicMock()
    cat.get_catalog.return_value = mock_catalog
    with container.core.catalog_service.override(providers.Object(cat)):
        resp = api_client.get(reverse("api_classic_state"))
    assert resp.status_code == 400
    assert resp.json()["error"] == "No game in progress"


@pytest.mark.django_db
def test_start_then_state_ok(api_client, mock_catalog):
    """Start (staff override) seeds the session, then state returns hints/guesses."""
    user = User.objects.create_user("staff1", password="x", is_staff=True)
    api_client.force_authenticate(user=user)

    cat = MagicMock()
    cat.get_catalog.return_value = mock_catalog
    game = MagicMock()
    game.select_secret.return_value = "Naruto"

    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.game_service.override(providers.Object(game)),
    ):
        start = api_client.post(
            reverse("api_classic_start"),
            {"media_type": "Anime", "override_secret": "Naruto"},
            format="json",
        )
        assert start.status_code == 200
        assert start.json()["status"] == "started"

        resp = api_client.get(reverse("api_classic_state"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["media_type"] == "Anime"
    assert data["game_over"] is False
    # game not over -> secret hidden
    assert data["secret_title"] is None
    assert "origin" in data["hints"]


@pytest.mark.django_db
def test_state_catalog_not_found(api_client):
    """State when catalog_service returns falsy -> 404 Catalog not found."""
    user = User.objects.create_user("staff2", password="x", is_staff=True)
    api_client.force_authenticate(user=user)

    full_catalog = {
        "title_to_full_data": {"Naruto": {"title": "Naruto"}},
        "titles": ["Naruto"],
        "title_to_index": {"Naruto": 1},
        "lookup": [{"id": 1, "title": "Naruto"}],
    }
    cat = MagicMock()
    game = MagicMock()
    # Start succeeds with a real catalog, then state sees an empty catalog.
    cat.get_catalog.side_effect = [full_catalog, None]
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.game_service.override(providers.Object(game)),
    ):
        api_client.post(
            reverse("api_classic_start"),
            {"media_type": "Anime", "override_secret": "Naruto"},
            format="json",
        )
        resp = api_client.get(reverse("api_classic_state"))
    assert resp.status_code == 404
    assert resp.json()["error"] == "Catalog not found"


@pytest.mark.django_db
def test_state_secret_data_not_found(api_client):
    """State when secret title missing from catalog data -> 404."""
    user = User.objects.create_user("staff3", password="x", is_staff=True)
    api_client.force_authenticate(user=user)

    start_catalog = {
        "title_to_full_data": {"Naruto": {"title": "Naruto"}},
        "titles": ["Naruto"],
        "title_to_index": {"Naruto": 1},
        "lookup": [{"id": 1, "title": "Naruto"}],
    }
    state_catalog = {
        "title_to_full_data": {},  # secret no longer present
        "titles": [],
        "title_to_index": {},
        "lookup": [],
    }
    cat = MagicMock()
    cat.get_catalog.side_effect = [start_catalog, state_catalog]
    game = MagicMock()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.game_service.override(providers.Object(game)),
    ):
        api_client.post(
            reverse("api_classic_start"),
            {"media_type": "Anime", "override_secret": "Naruto"},
            format="json",
        )
        resp = api_client.get(reverse("api_classic_state"))
    assert resp.status_code == 404
    assert resp.json()["error"] == "Secret title data not found"


# ---------------------------------------------------------------------------
# ClassicGameStartView
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_start_catalog_not_found(api_client, mock_catalog):
    cat = MagicMock()
    cat.get_catalog.return_value = None
    game = MagicMock()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.game_service.override(providers.Object(game)),
    ):
        resp = api_client.post(
            reverse("api_classic_start"), {"media_type": "Anime"}, format="json"
        )
    assert resp.status_code == 404
    assert resp.json()["error"] == "Catalog not found"


@pytest.mark.django_db
def test_start_select_secret_via_game_service(api_client, mock_catalog):
    """Non-staff start: secret chosen by game_service.select_secret."""
    cat = MagicMock()
    cat.get_catalog.return_value = mock_catalog
    game = MagicMock()
    game.select_secret.return_value = "Naruto"
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.game_service.override(providers.Object(game)),
    ):
        resp = api_client.post(
            reverse("api_classic_start"),
            {"media_type": "Anime", "difficulty": "Hard"},
            format="json",
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "started"
    assert data["difficulty"] == "Hard"
    assert data["is_ranked"] is False
    game.select_secret.assert_called_once()


@pytest.mark.django_db
def test_start_select_secret_failure(api_client, mock_catalog):
    cat = MagicMock()
    cat.get_catalog.return_value = mock_catalog
    game = MagicMock()
    game.select_secret.return_value = None
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.game_service.override(providers.Object(game)),
    ):
        resp = api_client.post(
            reverse("api_classic_start"), {"media_type": "Anime"}, format="json"
        )
    assert resp.status_code == 500
    assert resp.json()["error"] == "Failed to select secret title"


@pytest.mark.django_db
def test_start_non_staff_override_ignored(api_client, mock_catalog):
    """A non-staff user passing override_secret is logged and ignored."""
    user = User.objects.create_user("plain", password="x")
    api_client.force_authenticate(user=user)
    cat = MagicMock()
    cat.get_catalog.return_value = mock_catalog
    game = MagicMock()
    game.select_secret.return_value = "Bleach"
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.game_service.override(providers.Object(game)),
    ):
        resp = api_client.post(
            reverse("api_classic_start"),
            {"media_type": "Anime", "override_secret": "Naruto"},
            format="json",
        )
    assert resp.status_code == 200
    # game_service was used because override was ignored
    game.select_secret.assert_called_once()


# ---------------------------------------------------------------------------
# ClassicGameGuessView
# ---------------------------------------------------------------------------


def _seed_started_game(api_client, cat, game, media_type="Anime"):
    """Start a game as staff with a fixed secret so the session has state."""
    return api_client.post(
        reverse("api_classic_start"),
        {"media_type": media_type, "override_secret": "Naruto"},
        format="json",
    )


@pytest.mark.django_db
def test_guess_no_game(api_client, mock_catalog):
    cat = MagicMock()
    cat.get_catalog.return_value = mock_catalog
    game = MagicMock()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.game_service.override(providers.Object(game)),
    ):
        resp = api_client.post(
            reverse("api_classic_guess"), {"guess": "Naruto"}, format="json"
        )
    assert resp.status_code == 400
    assert resp.json()["error"] == "No game in progress"


@pytest.mark.django_db
def test_guess_missing_guess_field(api_client, mock_catalog):
    user = User.objects.create_user("staffg1", password="x", is_staff=True)
    api_client.force_authenticate(user=user)
    cat = MagicMock()
    cat.get_catalog.return_value = mock_catalog
    game = MagicMock()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.game_service.override(providers.Object(game)),
    ):
        _seed_started_game(api_client, cat, game)
        resp = api_client.post(reverse("api_classic_guess"), {}, format="json")
    assert resp.status_code == 400
    assert resp.json()["error"] == "Guess is required"


@pytest.mark.django_db
def test_guess_title_not_in_catalog(api_client, mock_catalog):
    user = User.objects.create_user("staffg2", password="x", is_staff=True)
    api_client.force_authenticate(user=user)
    cat = MagicMock()
    cat.get_catalog.return_value = mock_catalog
    game = MagicMock()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.game_service.override(providers.Object(game)),
    ):
        _seed_started_game(api_client, cat, game)
        resp = api_client.post(
            reverse("api_classic_guess"), {"guess": "Unknown Title"}, format="json"
        )
    assert resp.status_code == 400
    assert "not in catalog" in resp.json()["error"]


@pytest.mark.django_db
def test_guess_incorrect(api_client, mock_catalog):
    """A wrong guess returns a scored guess and keeps the game running."""
    user = User.objects.create_user("staffg3", password="x", is_staff=True)
    api_client.force_authenticate(user=user)
    cat = MagicMock()
    cat.get_catalog.return_value = mock_catalog
    game = MagicMock()
    game.check_title_match.return_value = False
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.game_service.override(providers.Object(game)),
    ):
        _seed_started_game(api_client, cat, game)
        resp = api_client.post(
            reverse("api_classic_guess"), {"guess": "Bleach"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is False
    assert data["game_over"] is False
    assert data["latest_guess"]["title"] == "Bleach"
    assert data["guess_count"] == 1


@pytest.mark.django_db
def test_guess_correct_authenticated_creates_session(api_client, mock_catalog):
    """A correct guess by an authenticated user ends the game, awards a win,
    and persists a GameplaySession row."""
    from animetix.models import GameplaySession

    user = User.objects.create_user("winner", password="x", is_staff=True)
    api_client.force_authenticate(user=user)

    # profile.add_win returns an achievement with attributes used by the view
    ach = MagicMock()
    ach.name = "First Win"
    ach.description = "You won"
    ach.xp_reward = 10
    ach.badge_url = "http://badge.png"
    # The view accesses request.user.profile.add_win; ensure a profile exists.
    profile = getattr(user, "profile", None)
    if profile is None:
        pytest.skip("User has no profile relation configured")
    profile.add_win = MagicMock(return_value=[ach])

    cat = MagicMock()
    cat.get_catalog.return_value = mock_catalog
    game = MagicMock()
    game.check_title_match.return_value = True
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.game_service.override(providers.Object(game)),
    ):
        _seed_started_game(api_client, cat, game)
        resp = api_client.post(
            reverse("api_classic_guess"), {"guess": "Naruto"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is True
    assert data["game_over"] is True
    assert data["secret_title"] == "Naruto"
    assert data["latest_guess"]["score"] == 100.0
    assert GameplaySession.objects.filter(target_item="Naruto", was_won=True).exists()


@pytest.mark.django_db
def test_guess_when_game_over(api_client, mock_catalog):
    """A second correct guess after game_over returns 400 Game already over."""
    user = User.objects.create_user("staffg4", password="x", is_staff=True)
    api_client.force_authenticate(user=user)
    profile = getattr(user, "profile", None)
    if profile is not None:
        profile.add_win = MagicMock(return_value=[])

    cat = MagicMock()
    cat.get_catalog.return_value = mock_catalog
    game = MagicMock()
    game.check_title_match.return_value = True
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.game_service.override(providers.Object(game)),
    ):
        _seed_started_game(api_client, cat, game)
        api_client.post(
            reverse("api_classic_guess"), {"guess": "Naruto"}, format="json"
        )
        resp = api_client.post(
            reverse("api_classic_guess"), {"guess": "Naruto"}, format="json"
        )
    assert resp.status_code == 400
    assert resp.json()["error"] == "Game already over"


# ---------------------------------------------------------------------------
# ClassicGameRevealView
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_reveal_no_game(api_client, mock_catalog):
    cat = MagicMock()
    cat.get_catalog.return_value = mock_catalog
    with container.core.catalog_service.override(providers.Object(cat)):
        resp = api_client.post(
            reverse("api_classic_reveal"), {"hint_type": "origin"}, format="json"
        )
    assert resp.status_code == 400
    assert resp.json()["error"] == "No game in progress"


@pytest.mark.django_db
def test_reveal_missing_hint_type(api_client, mock_catalog):
    user = User.objects.create_user("staffr1", password="x", is_staff=True)
    api_client.force_authenticate(user=user)
    cat = MagicMock()
    cat.get_catalog.return_value = mock_catalog
    game = MagicMock()
    game.select_secret.return_value = "Naruto"
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.game_service.override(providers.Object(game)),
    ):
        _seed_started_game(api_client, cat, game)
        resp = api_client.post(reverse("api_classic_reveal"), {}, format="json")
    assert resp.status_code == 400
    # Missing and unknown hint types share one rejection message.
    assert resp.json()["error"] == "Invalid hint type"


@pytest.mark.django_db
def test_reveal_ok(api_client, mock_catalog):
    user = User.objects.create_user("staffr2", password="x", is_staff=True)
    api_client.force_authenticate(user=user)
    cat = MagicMock()
    cat.get_catalog.return_value = mock_catalog
    game = MagicMock()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.game_service.override(providers.Object(game)),
    ):
        _seed_started_game(api_client, cat, game)
        # Hints unlock progressively (n-th hint after n*step guesses, step=5);
        # "origin" is the 2nd hint, so seed 10 guesses to make it revealable.
        session = api_client.session
        session["guesses"] = [{"title": "x", "is_correct": False} for _ in range(10)]
        session.save()
        resp = api_client.post(
            reverse("api_classic_reveal"), {"hint_type": "origin"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "origin" in data["revealed_hints"]
    assert "hints" in data
