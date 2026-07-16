"""Coverage tests for animetix.api.games.paradox.

Exercises the Paradox mode endpoints (state / start / move) against the real
Django session. The DI ``catalog_service`` / ``paradox_service`` /
``usage_port`` providers are mocked via instance-level container overrides.

The view stores its game state through ``paradox_service.get_state(port)`` /
``save_state``; because the service itself is a mock, ``get_state`` returns a
``MagicMock`` whose attributes the test controls to drive each branch.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from animetix.containers import container
from dependency_injector import providers
from django.contrib.auth.models import User
from django.urls import reverse


@pytest.fixture(autouse=True)
def _wire_container():
    # See test_emoji_coverage for the rationale: re-wire the view module so @inject
    # markers bind to live instance providers; never call reset_override (it detaches
    # the core->persistence sub-container link on this dependency_injector version).
    import animetix.api.games.paradox as paradox_mod

    container.wire(modules=[paradox_mod])
    yield


@pytest.fixture
def mock_catalog():
    return {
        "title_to_full_data": {
            "A": {"image": "a.jpg"},
            "B": {"image": "b.jpg"},
            "C": {"image": "c.jpg"},
        },
        "title_to_index": {"A": 1, "B": 2, "C": 3},
    }


def _state(**kwargs):
    """A dict standing in for the paradox session state (the view reads it with
    ``.get()`` — session state is a dict, not an object)."""
    defaults = dict(
        answer=None,
        media="Anime",
        options=[],
        scenario="",
        reasoning="",
        game_over=False,
        is_daily=False,
    )
    defaults.update(kwargs)
    return defaults


# --------------------------------------------------------------------------- #
# ParadoxGameStateView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_state_no_game(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    paradox = MagicMock()
    paradox.get_state.return_value = _state(answer=None)
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.paradox_service.override(providers.Object(paradox)),
    ):
        resp = api_client.get(reverse("api_paradox_state"))
    assert resp.status_code == 400
    assert resp.json()["error"] == "No game in progress"


@pytest.mark.django_db
def test_state_in_progress(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    paradox = MagicMock()
    paradox.get_state.return_value = _state(
        answer="C", media="Anime", options=["A", "B", "C"], scenario="why?"
    )
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.paradox_service.override(providers.Object(paradox)),
    ):
        resp = api_client.get(reverse("api_paradox_state"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["scenario"] == "why?"
    assert {i["title"] for i in data["items"]} == {"A", "B", "C"}
    assert data["items"][0]["id"] in (1, 2, 3)


# --------------------------------------------------------------------------- #
# ParadoxGameStartView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_start_quota_exceeded(api_client, mock_catalog):
    user = User.objects.create_user("pq", password="x")
    api_client.force_authenticate(user=user)
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    paradox = MagicMock()
    usage = MagicMock()
    usage.check_quota.return_value = False
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.paradox_service.override(providers.Object(paradox)),
        container.infrastructure.usage_port.override(providers.Object(usage)),
    ):
        resp = api_client.post(
            reverse("api_paradox_start"), {"media_type": "Anime"}, format="json"
        )
    assert resp.status_code == 403
    assert resp.json()["error"] == "Daily AI quota exceeded."


@pytest.mark.django_db
def test_start_catalog_not_found(api_client):
    user = User.objects.create_user("pc", password="x")
    api_client.force_authenticate(user=user)
    cat = MagicMock()
    cat.load_data.return_value = None
    paradox = MagicMock()
    usage = MagicMock()
    usage.check_quota.return_value = True
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.paradox_service.override(providers.Object(paradox)),
        container.infrastructure.usage_port.override(providers.Object(usage)),
    ):
        resp = api_client.post(
            reverse("api_paradox_start"), {"media_type": "Anime"}, format="json"
        )
    assert resp.status_code == 404
    assert resp.json()["error"] == "Catalog not found"


@pytest.mark.django_db
def test_start_prepare_failure(api_client, mock_catalog):
    user = User.objects.create_user("pp", password="x")
    api_client.force_authenticate(user=user)
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    paradox = MagicMock()
    paradox.prepare_challenge.return_value = None  # < 3 -> 500
    usage = MagicMock()
    usage.check_quota.return_value = True
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.paradox_service.override(providers.Object(paradox)),
        container.infrastructure.usage_port.override(providers.Object(usage)),
    ):
        resp = api_client.post(
            reverse("api_paradox_start"), {"media_type": "Anime"}, format="json"
        )
    assert resp.status_code == 500
    assert resp.json()["error"] == "Failed to prepare paradox challenge"


@pytest.mark.django_db
def test_start_success(api_client, mock_catalog):
    user = User.objects.create_user("ps", password="x")
    api_client.force_authenticate(user=user)
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    paradox = MagicMock()
    paradox.prepare_challenge.return_value = ("A", "B", "C")
    paradox.generate_logic.return_value = SimpleNamespace(
        reasoning="because", scenario="the scene"
    )
    paradox.get_state.return_value = _state()
    usage = MagicMock()
    usage.check_quota.return_value = True
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.paradox_service.override(providers.Object(paradox)),
        container.infrastructure.usage_port.override(providers.Object(usage)),
    ):
        resp = api_client.post(
            reverse("api_paradox_start"), {"media_type": "Anime"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "started"
    assert data["scenario"] == "the scene"
    assert {i["title"] for i in data["items"]} == {"A", "B", "C"}
    usage.log_usage.assert_called_once()
    paradox.save_state.assert_called_once()


# --------------------------------------------------------------------------- #
# ParadoxGameGuessView (move)
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_guess_no_game(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    paradox = MagicMock()
    paradox.get_state.return_value = _state(answer=None)
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.paradox_service.override(providers.Object(paradox)),
    ):
        resp = api_client.post(
            reverse("api_paradox_guess"), {"guess": "A"}, format="json"
        )
    assert resp.status_code == 400
    assert resp.json()["error"] == "No game in progress"


@pytest.mark.django_db
def test_guess_already_over(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    paradox = MagicMock()
    paradox.get_state.return_value = _state(answer="C", game_over=True)
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.paradox_service.override(providers.Object(paradox)),
    ):
        resp = api_client.post(
            reverse("api_paradox_guess"), {"guess": "A"}, format="json"
        )
    assert resp.status_code == 400
    assert resp.json()["error"] == "Game already over"


@pytest.mark.django_db
def test_guess_missing_guess(api_client, mock_catalog):
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    paradox = MagicMock()
    paradox.get_state.return_value = _state(
        answer="C", options=["A", "B", "C"], media="Anime"
    )
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.paradox_service.override(providers.Object(paradox)),
    ):
        resp = api_client.post(reverse("api_paradox_guess"), {}, format="json")
    assert resp.status_code == 400
    assert resp.json()["error"] == "Guess is required"


@pytest.mark.django_db
def test_guess_by_intruder_id_incorrect(api_client, mock_catalog):
    """No guess title but intruder_id maps back to a title via title_to_index."""
    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    paradox = MagicMock()
    paradox.get_state.return_value = _state(
        answer="C", options=["A", "B", "C"], media="Anime"
    )
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.paradox_service.override(providers.Object(paradox)),
    ):
        resp = api_client.post(
            reverse("api_paradox_guess"), {"intruder_id": 1}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is False  # id 1 -> "A", answer is "C"
    assert data["answer"] == "C"
    assert data["game_over"] is True


@pytest.mark.django_db
def test_guess_correct_authenticated_creates_session(api_client, mock_catalog):
    from animetix.models import GameplaySession

    user = User.objects.create_user("pwin", password="x")
    api_client.force_authenticate(user=user)
    ach = MagicMock()
    ach.name = "P Win"
    ach.description = "d"
    ach.xp_reward = 5
    ach.badge_url = "http://b.png"
    user.profile.add_win = MagicMock(return_value=[ach])

    cat = MagicMock()
    cat.load_data.return_value = mock_catalog
    paradox = MagicMock()
    paradox.get_state.return_value = _state(
        answer="C", options=["A", "B", "C"], media="Anime", reasoning="r"
    )
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.paradox_service.override(providers.Object(paradox)),
    ):
        resp = api_client.post(
            reverse("api_paradox_guess"), {"guess": "C"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is True
    assert data["game_over"] is True
    assert data["newly_unlocked_achievements"][0]["name"] == "P Win"
    assert GameplaySession.objects.filter(target_item="C", was_won=True).exists()
