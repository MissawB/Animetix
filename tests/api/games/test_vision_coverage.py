"""Coverage tests for animetix.api.games.vision.

Exercises the Vision Quest endpoints (state / start / guess) against the real
Django session. The DI ``catalog_service`` / ``vision_service`` /
``guardrail_service`` providers (core) and the ``usage_port`` (infrastructure)
are mocked via instance-level container overrides.

``vision_service`` is a mock; ``get_state`` returns a controllable
``SimpleNamespace`` standing in for the Vision Quest state object.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from animetix.containers import container
from dependency_injector import providers
from django.contrib.auth.models import User
from django.urls import reverse


def _state(**kwargs):
    defaults = dict(
        secret_id=None,
        secret_title=None,
        image_url=None,
        media_type="Anime",
        is_daily=False,
        game_over=False,
        guesses=[],
        best_score=0,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


_SECRET = {"id": 7, "title": "Naruto", "image": "http://img.jpg"}


# --------------------------------------------------------------------------- #
# VisionGameStateView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_state_no_game(api_client):
    vision = MagicMock()
    vision.get_state.return_value = _state(secret_id=None)
    with container.core.vision_service.override(providers.Object(vision)):
        resp = api_client.get(reverse("api_vision_state"))
    assert resp.status_code == 400
    assert resp.json()["error"] == "No game in progress"


@pytest.mark.django_db
def test_state_in_progress_hides_secret(api_client):
    vision = MagicMock()
    vision.get_state.return_value = _state(
        secret_id="7",
        secret_title="Naruto",
        image_url="http://img.jpg",
        game_over=False,
    )
    with container.core.vision_service.override(providers.Object(vision)):
        resp = api_client.get(reverse("api_vision_state"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["image_url"] == "http://img.jpg"
    assert data["game_over"] is False
    assert data["secret_title"] is None  # hidden while running


@pytest.mark.django_db
def test_state_game_over_reveals_secret(api_client):
    vision = MagicMock()
    vision.get_state.return_value = _state(
        secret_id="7", secret_title="Naruto", game_over=True
    )
    with container.core.vision_service.override(providers.Object(vision)):
        resp = api_client.get(reverse("api_vision_state"))
    assert resp.status_code == 200
    assert resp.json()["secret_title"] == "Naruto"


# --------------------------------------------------------------------------- #
# VisionGameStartView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_start_catalog_not_found(api_client):
    cat = MagicMock()
    cat.load_data.return_value = None
    vision = MagicMock()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.vision_service.override(providers.Object(vision)),
    ):
        resp = api_client.post(
            reverse("api_vision_start"), {"media_type": "Anime"}, format="json"
        )
    assert resp.status_code == 404
    assert resp.json()["error"] == "Catalog not found"


@pytest.mark.django_db
def test_start_select_secret_failure(api_client):
    cat = MagicMock()
    cat.load_data.return_value = {"title_to_full_data": {}}
    vision = MagicMock()
    vision.select_secret.return_value = None
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.vision_service.override(providers.Object(vision)),
    ):
        resp = api_client.post(
            reverse("api_vision_start"), {"media_type": "Anime"}, format="json"
        )
    assert resp.status_code == 500
    assert resp.json()["error"] == "Failed to select secret"


@pytest.mark.django_db
def test_start_random_success(api_client):
    cat = MagicMock()
    cat.load_data.return_value = {"title_to_full_data": {}}
    vision = MagicMock()
    vision.select_secret.return_value = _SECRET
    vision.get_state.return_value = _state()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.vision_service.override(providers.Object(vision)),
    ):
        resp = api_client.post(
            reverse("api_vision_start"), {"media_type": "Anime"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["image_url"] == "http://img.jpg"
    assert data["game_over"] is False
    assert data["best_score"] == 0
    vision.save_state.assert_called_once()


@pytest.mark.django_db
def test_start_daily_uses_session_secret(api_client):
    cat = MagicMock()
    cat.load_data.return_value = {"title_to_full_data": {"Naruto": _SECRET}}
    vision = MagicMock()
    vision.get_state.return_value = _state()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.vision_service.override(providers.Object(vision)),
    ):
        # First non-daily start to seed media_type, then daily start reads
        # secret_title from the session port (None -> not found -> 500).
        resp = api_client.post(
            reverse("api_vision_start"),
            {"media_type": "Anime", "is_daily": True},
            format="json",
        )
    # secret_title not seeded in session -> .get(None) -> None -> 500
    assert resp.status_code == 500
    assert resp.json()["error"] == "Failed to select secret"
    # The daily branch must not call select_secret.
    vision.select_secret.assert_not_called()


# --------------------------------------------------------------------------- #
# VisionGameGuessView
# --------------------------------------------------------------------------- #
def _auth(api_client, name="visionplayer"):
    user = User.objects.create_user(name, password="x")
    api_client.force_authenticate(user=user)
    return user


@pytest.mark.django_db
def test_guess_requires_authentication(api_client):
    """Unauthenticated guess -> 401/403 (IsAuthenticated)."""
    resp = api_client.post(
        reverse("api_vision_guess"), {"description": "a ninja"}, format="json"
    )
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_guess_no_game(api_client):
    _auth(api_client, "vg_nogame")
    vision = MagicMock()
    vision.get_state.return_value = _state(secret_id=None)
    guard = MagicMock()
    usage = MagicMock()
    with (
        container.core.vision_service.override(providers.Object(vision)),
        container.core.guardrail_service.override(providers.Object(guard)),
        container.infrastructure.usage_port.override(providers.Object(usage)),
    ):
        resp = api_client.post(
            reverse("api_vision_guess"), {"description": "a ninja"}, format="json"
        )
    assert resp.status_code == 400
    assert resp.json()["error"] == "No game in progress"


@pytest.mark.django_db
def test_guess_game_over(api_client):
    _auth(api_client, "vg_over")
    vision = MagicMock()
    vision.get_state.return_value = _state(secret_id="7", game_over=True)
    guard = MagicMock()
    usage = MagicMock()
    with (
        container.core.vision_service.override(providers.Object(vision)),
        container.core.guardrail_service.override(providers.Object(guard)),
        container.infrastructure.usage_port.override(providers.Object(usage)),
    ):
        resp = api_client.post(
            reverse("api_vision_guess"), {"description": "a ninja"}, format="json"
        )
    assert resp.status_code == 400
    assert resp.json()["error"] == "Game already over"


@pytest.mark.django_db
def test_guess_quota_exceeded(api_client):
    _auth(api_client, "vg_quota")
    vision = MagicMock()
    vision.get_state.return_value = _state(secret_id="7", secret_title="Naruto")
    guard = MagicMock()
    usage = MagicMock()
    usage.check_quota.return_value = False
    with (
        container.core.vision_service.override(providers.Object(vision)),
        container.core.guardrail_service.override(providers.Object(guard)),
        container.infrastructure.usage_port.override(providers.Object(usage)),
    ):
        resp = api_client.post(
            reverse("api_vision_guess"), {"description": "a ninja"}, format="json"
        )
    assert resp.status_code == 403
    assert resp.json()["error"] == "Daily AI quota exceeded."


@pytest.mark.django_db
def test_guess_invalid_form(api_client):
    """Missing description -> form invalid -> 400 with field errors."""
    _auth(api_client, "vg_form")
    vision = MagicMock()
    vision.get_state.return_value = _state(secret_id="7", secret_title="Naruto")
    guard = MagicMock()
    usage = MagicMock()
    usage.check_quota.return_value = True
    with (
        container.core.vision_service.override(providers.Object(vision)),
        container.core.guardrail_service.override(providers.Object(guard)),
        container.infrastructure.usage_port.override(providers.Object(usage)),
    ):
        resp = api_client.post(reverse("api_vision_guess"), {}, format="json")
    assert resp.status_code == 400
    assert "description" in resp.json()


@pytest.mark.django_db
def test_guess_unsafe_input_blocked(api_client):
    _auth(api_client, "vg_unsafe")
    vision = MagicMock()
    vision.get_state.return_value = _state(secret_id="7", secret_title="Naruto")
    guard = MagicMock()
    guard.validate_input.return_value = {"is_safe": False, "reason": "Nope"}
    usage = MagicMock()
    usage.check_quota.return_value = True
    with (
        container.core.vision_service.override(providers.Object(vision)),
        container.core.guardrail_service.override(providers.Object(guard)),
        container.infrastructure.usage_port.override(providers.Object(usage)),
    ):
        resp = api_client.post(
            reverse("api_vision_guess"), {"description": "bad text"}, format="json"
        )
    assert resp.status_code == 400
    assert resp.json()["error"] == "Nope"


@pytest.mark.django_db
def test_guess_incorrect_keeps_running(api_client):
    _auth(api_client, "vg_wrong")
    vision = MagicMock()
    vision.get_state.return_value = _state(
        secret_id="7", secret_title="Naruto", best_score=80, guesses=[]
    )
    vision.calculate_score.return_value = 40
    guard = MagicMock()
    guard.validate_input.return_value = {"is_safe": True}
    usage = MagicMock()
    usage.check_quota.return_value = True
    with (
        container.core.vision_service.override(providers.Object(vision)),
        container.core.guardrail_service.override(providers.Object(guard)),
        container.infrastructure.usage_port.override(providers.Object(usage)),
    ):
        resp = api_client.post(
            reverse("api_vision_guess"), {"description": "a ninja"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] == 40
    assert data["is_correct"] is False
    assert data["is_new_best"] is False  # 40 < best 80
    assert data["best_score"] == 80
    assert data["game_over"] is False
    usage.log_usage.assert_called_once()


@pytest.mark.django_db
def test_guess_new_best_not_correct(api_client):
    _auth(api_client, "vg_best")
    vision = MagicMock()
    vision.get_state.return_value = _state(
        secret_id="7", secret_title="Naruto", best_score=10, guesses=[]
    )
    vision.calculate_score.return_value = 50
    guard = MagicMock()
    guard.validate_input.return_value = {"is_safe": True}
    usage = MagicMock()
    usage.check_quota.return_value = True
    with (
        container.core.vision_service.override(providers.Object(vision)),
        container.core.guardrail_service.override(providers.Object(guard)),
        container.infrastructure.usage_port.override(providers.Object(usage)),
    ):
        resp = api_client.post(
            reverse("api_vision_guess"), {"description": "a ninja"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_new_best"] is True
    assert data["best_score"] == 50
    assert data["is_correct"] is False


@pytest.mark.django_db
def test_guess_correct_creates_session(api_client):
    from animetix.models import GameplaySession

    user = _auth(api_client, "vg_win")
    ach = MagicMock()
    ach.name = "V Win"
    ach.description = "d"
    ach.xp_reward = 5
    ach.badge_url = "http://b.png"
    user.profile.add_win = MagicMock(return_value=[ach])

    vision = MagicMock()
    vision.get_state.return_value = _state(
        secret_id="7", secret_title="Naruto", best_score=0, guesses=[]
    )
    vision.calculate_score.return_value = 95
    guard = MagicMock()
    guard.validate_input.return_value = {"is_safe": True}
    usage = MagicMock()
    usage.check_quota.return_value = True
    with (
        container.core.vision_service.override(providers.Object(vision)),
        container.core.guardrail_service.override(providers.Object(guard)),
        container.infrastructure.usage_port.override(providers.Object(usage)),
    ):
        resp = api_client.post(
            reverse("api_vision_guess"), {"description": "a ninja"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is True
    assert data["game_over"] is True
    assert data["secret_title"] == "Naruto"
    assert data["newly_unlocked_achievements"][0]["name"] == "V Win"
    assert GameplaySession.objects.filter(target_item="Naruto", was_won=True).exists()


@pytest.mark.django_db
def test_guess_correct_add_win_raises_is_handled(api_client):
    from animetix.models import GameplaySession

    user = _auth(api_client, "vg_winerr")
    user.profile.add_win = MagicMock(side_effect=RuntimeError("boom"))

    vision = MagicMock()
    vision.get_state.return_value = _state(
        secret_id="7", secret_title="Naruto", best_score=0, guesses=[]
    )
    vision.calculate_score.return_value = 90
    guard = MagicMock()
    guard.validate_input.return_value = {"is_safe": True}
    usage = MagicMock()
    usage.check_quota.return_value = True
    with (
        container.core.vision_service.override(providers.Object(vision)),
        container.core.guardrail_service.override(providers.Object(guard)),
        container.infrastructure.usage_port.override(providers.Object(usage)),
    ):
        resp = api_client.post(
            reverse("api_vision_guess"), {"description": "a ninja"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is True
    assert data["newly_unlocked_achievements"] == []
    assert GameplaySession.objects.filter(target_item="Naruto", was_won=True).exists()


@pytest.mark.django_db
def test_guess_unexpected_exception_returns_500(api_client):
    _auth(api_client, "vg_err")
    vision = MagicMock()
    vision.get_state.return_value = _state(secret_id="7", secret_title="Naruto")
    vision.calculate_score.side_effect = RuntimeError("score boom")
    guard = MagicMock()
    guard.validate_input.return_value = {"is_safe": True}
    usage = MagicMock()
    usage.check_quota.return_value = True
    with (
        container.core.vision_service.override(providers.Object(vision)),
        container.core.guardrail_service.override(providers.Object(guard)),
        container.infrastructure.usage_port.override(providers.Object(usage)),
    ):
        resp = api_client.post(
            reverse("api_vision_guess"), {"description": "a ninja"}, format="json"
        )
    assert resp.status_code == 500
    assert resp.json()["error"] == "Internal server error"
