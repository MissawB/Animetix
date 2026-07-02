"""Coverage tests for animetix.api.games.covertest.

Exercises the Covertest mode endpoints (state / start / guess) against the real
Django session. The DI ``catalog_service`` / ``cover_test_service`` /
``game_service`` providers are mocked via instance-level container overrides.

``cover_test_service`` is a mock; ``get_state`` returns a controllable attribute
bag standing in for the cover-test State object.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from animetix.containers import container
from dependency_injector import providers
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def _wire_container():
    # See test_emoji_coverage for the rationale: re-wire the view module so @inject
    # markers bind to live instance providers; never call reset_override (it detaches
    # the core->persistence sub-container link on this dependency_injector version).
    import animetix.api.games.covertest as covertest_mod

    container.wire(modules=[covertest_mod])
    yield


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def mock_catalog():
    return {
        "title_to_full_data": {
            "Berserk": {"image": "b.jpg"},
            "Vinland": {"image": "v.jpg"},
        }
    }


def _state(**kwargs):
    defaults = dict(
        secret=None,
        url=None,
        locale=None,
        volume=None,
        guesses=[],
        game_over=False,
        is_daily=False,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


_COVER = {
    "manga_title": "Berserk",
    "cover_url": "http://cover.jpg",
    "locale": "ja",
    "volume": 1,
}


# --------------------------------------------------------------------------- #
# CovertestGameStateView (auto-start)
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_state_auto_start_random(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    cover = MagicMock()
    cover.get_state.return_value = _state(secret=None)
    cover.get_random_cover.return_value = _COVER
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.cover_test_service.override(providers.Object(cover)),
    ):
        resp = api_client.get(reverse("api_covertest_state"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["cover_url"] == "http://cover.jpg"
    assert data["locale"] == "ja"
    assert data["secret_title"] is None  # hidden while running


@pytest.mark.django_db
def test_state_auto_start_daily(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    cover = MagicMock()
    cover.get_state.return_value = _state(secret=None)
    cover.get_daily_cover.return_value = _COVER
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.cover_test_service.override(providers.Object(cover)),
    ):
        resp = api_client.get(reverse("api_covertest_state") + "?is_daily=true")
    assert resp.status_code == 200
    assert resp.json()["is_daily"] is True
    cover.get_daily_cover.assert_called_once()


@pytest.mark.django_db
def test_state_auto_start_fails(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    cover = MagicMock()
    cover.get_state.return_value = _state(secret=None)
    cover.get_random_cover.return_value = None
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.cover_test_service.override(providers.Object(cover)),
    ):
        resp = api_client.get(reverse("api_covertest_state"))
    assert resp.status_code == 400
    assert "auto-start failed" in resp.json()["error"]


# --------------------------------------------------------------------------- #
# CovertestGameStartView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_start_catalog_not_found(api_client):
    cat = MagicMock()
    cat.load_data.return_value = None
    cover = MagicMock()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.cover_test_service.override(providers.Object(cover)),
    ):
        resp = api_client.post(reverse("api_covertest_start"), {}, format="json")
    assert resp.status_code == 404
    assert resp.json()["error"] == "Catalog not found"


@pytest.mark.django_db
def test_start_no_cover(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    cover = MagicMock()
    cover.get_random_cover.return_value = None
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.cover_test_service.override(providers.Object(cover)),
    ):
        resp = api_client.post(reverse("api_covertest_start"), {}, format="json")
    assert resp.status_code == 500
    assert resp.json()["error"] == "Failed to select cover"


@pytest.mark.django_db
def test_start_success(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    cover = MagicMock()
    cover.get_random_cover.return_value = _COVER
    cover.get_state.return_value = _state()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.cover_test_service.override(providers.Object(cover)),
    ):
        resp = api_client.post(reverse("api_covertest_start"), {}, format="json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cover_url"] == "http://cover.jpg"
    assert data["game_over"] is False


# --------------------------------------------------------------------------- #
# CovertestGameGuessView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_guess_no_game(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    cover = MagicMock()
    cover.get_state.return_value = _state(secret=None)
    game = MagicMock()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.cover_test_service.override(providers.Object(cover)),
        container.core.game_service.override(providers.Object(game)),
    ):
        resp = api_client.post(
            reverse("api_covertest_guess"), {"guess": "Berserk"}, format="json"
        )
    assert resp.status_code == 400
    assert resp.json()["error"] == "No game in progress"


@pytest.mark.django_db
def test_guess_already_over(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    cover = MagicMock()
    cover.get_state.return_value = _state(secret="Berserk", game_over=True)
    game = MagicMock()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.cover_test_service.override(providers.Object(cover)),
        container.core.game_service.override(providers.Object(game)),
    ):
        resp = api_client.post(
            reverse("api_covertest_guess"), {"guess": "Berserk"}, format="json"
        )
    assert resp.status_code == 400
    assert resp.json()["error"] == "Game already over"


@pytest.mark.django_db
def test_guess_missing_guess(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    cover = MagicMock()
    cover.get_state.return_value = _state(secret="Berserk")
    game = MagicMock()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.cover_test_service.override(providers.Object(cover)),
        container.core.game_service.override(providers.Object(game)),
    ):
        resp = api_client.post(reverse("api_covertest_guess"), {}, format="json")
    assert resp.status_code == 400
    assert resp.json()["error"] == "Guess is required"


@pytest.mark.django_db
def test_guess_incorrect(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    cover = MagicMock()
    cover.get_state.return_value = _state(secret="Berserk", guesses=[])
    game = MagicMock()
    game.check_title_match.return_value = False
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.cover_test_service.override(providers.Object(cover)),
        container.core.game_service.override(providers.Object(game)),
    ):
        resp = api_client.post(
            reverse("api_covertest_guess"), {"guess": "Vinland"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is False
    assert data["game_over"] is False
    assert data["guesses"][0]["title"] == "Vinland"


@pytest.mark.django_db
def test_guess_correct_authenticated_creates_session(api_client, mock_catalog):
    from animetix.models import GameplaySession

    user = User.objects.create_user("cwin", password="x")
    api_client.force_authenticate(user=user)
    ach = MagicMock()
    ach.name = "C Win"
    ach.description = "d"
    ach.xp_reward = 5
    ach.badge_url = "http://b.png"
    user.profile.add_win = MagicMock(return_value=[ach])

    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    cover = MagicMock()
    cover.get_state.return_value = _state(secret="Berserk", guesses=[])
    game = MagicMock()
    game.check_title_match.return_value = True
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.cover_test_service.override(providers.Object(cover)),
        container.core.game_service.override(providers.Object(game)),
    ):
        resp = api_client.post(
            reverse("api_covertest_guess"), {"guess": "Berserk"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is True
    assert data["game_over"] is True
    assert data["secret_title"] == "Berserk"
    assert data["newly_unlocked_achievements"][0]["name"] == "C Win"
    assert GameplaySession.objects.filter(target_item="Berserk", was_won=True).exists()
