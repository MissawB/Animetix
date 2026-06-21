"""Coverage tests for animetix.api.games.akinetix.

Exercises the Akinetix endpoints (state / start / answer / confirm) against the
real Django session. The DI ``catalog_service`` / ``akinetix_service`` providers
are mocked via instance-level container overrides.

``akinetix_service`` is a mock; ``get_state`` / ``start_new_game`` /
``process_answer`` return controllable ``SimpleNamespace`` objects standing in
for the Akinetix state.
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


def _state(**kwargs):
    defaults = dict(
        current_q=None,
        history=[],
        game_over=False,
        ai_guess=None,
        is_daily=False,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


_CAT = {"db": [{"name": "Goku"}, {"name": "Luffy"}]}


# --------------------------------------------------------------------------- #
# AkinetixGameStateView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_state_no_game(api_client):
    ak = MagicMock()
    ak.get_state.return_value = _state(current_q=None)
    with container.core.akinetix_service.override(providers.Object(ak)):
        resp = api_client.get(reverse("api_akinetix_state"))
    assert resp.status_code == 400
    assert resp.json()["error"] == "No game in progress"


@pytest.mark.django_db
def test_state_in_progress_with_model_dump_history(api_client):
    """history holding a model_dump-capable object exercises that branch."""
    q = MagicMock()
    q.model_dump.return_value = {"q": "Is it a hero?", "a": "OUI"}
    ak = MagicMock()
    ak.get_state.return_value = _state(
        current_q="Is it a villain?", history=[q], ai_guess=None
    )
    with container.core.akinetix_service.override(providers.Object(ak)):
        resp = api_client.get(reverse("api_akinetix_state"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_question"] == "Is it a villain?"
    assert data["history"][0] == {"q": "Is it a hero?", "a": "OUI"}
    assert data["game_over"] is False


# --------------------------------------------------------------------------- #
# AkinetixGameStartView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_start_invalid_serializer(api_client):
    ak = MagicMock()
    cat = MagicMock()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.akinetix_service.override(providers.Object(ak)),
    ):
        resp = api_client.post(
            reverse("api_akinetix_start"),
            {"media_type": "NotAType"},
            format="json",
        )
    assert resp.status_code == 400
    assert "media_type" in resp.json()


@pytest.mark.django_db
def test_start_catalog_not_found(api_client):
    cat = MagicMock()
    cat.load_data.return_value = None
    ak = MagicMock()
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.akinetix_service.override(providers.Object(ak)),
    ):
        resp = api_client.post(
            reverse("api_akinetix_start"), {"media_type": "Anime"}, format="json"
        )
    assert resp.status_code == 404
    assert resp.json()["error"] == "Catalog not found"


@pytest.mark.django_db
def test_start_success(api_client):
    cat = MagicMock()
    cat.load_data.return_value = _CAT
    ak = MagicMock()
    ak.start_new_game.return_value = _state(current_q="First question?", history=[])
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.akinetix_service.override(providers.Object(ak)),
    ):
        resp = api_client.post(
            reverse("api_akinetix_start"), {"media_type": "Anime"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "started"
    assert data["current_question"] == "First question?"
    ak.save_state.assert_called_once()


@pytest.mark.django_db
def test_start_daily_sets_flag(api_client):
    cat = MagicMock()
    cat.load_data.return_value = _CAT
    ak = MagicMock()
    ak.start_new_game.return_value = _state(current_q="Q?", history=[], is_daily=False)
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.akinetix_service.override(providers.Object(ak)),
    ):
        resp = api_client.post(
            reverse("api_akinetix_start"),
            {"media_type": "Anime", "is_daily": True},
            format="json",
        )
    assert resp.status_code == 200
    assert resp.json()["is_daily"] is True


# --------------------------------------------------------------------------- #
# AkinetixGameAnswerView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_answer_no_game(api_client):
    cat = MagicMock()
    ak = MagicMock()
    ak.get_state.return_value = _state(current_q=None)
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.akinetix_service.override(providers.Object(ak)),
    ):
        resp = api_client.post(
            reverse("api_akinetix_answer"), {"answer": "OUI"}, format="json"
        )
    assert resp.status_code == 400
    assert resp.json()["error"] == "No game in progress"


@pytest.mark.django_db
def test_answer_game_over(api_client):
    cat = MagicMock()
    ak = MagicMock()
    ak.get_state.return_value = _state(current_q="Q?", game_over=True)
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.akinetix_service.override(providers.Object(ak)),
    ):
        resp = api_client.post(
            reverse("api_akinetix_answer"), {"answer": "OUI"}, format="json"
        )
    assert resp.status_code == 400
    assert resp.json()["error"] == "Game already over"


@pytest.mark.django_db
def test_answer_invalid_serializer(api_client):
    cat = MagicMock()
    ak = MagicMock()
    ak.get_state.return_value = _state(current_q="Q?")
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.akinetix_service.override(providers.Object(ak)),
    ):
        resp = api_client.post(
            reverse("api_akinetix_answer"), {"answer": "MAYBE"}, format="json"
        )
    assert resp.status_code == 400
    assert "answer" in resp.json()


@pytest.mark.django_db
def test_answer_catalog_not_found(api_client):
    cat = MagicMock()
    cat.load_data.return_value = None
    ak = MagicMock()
    ak.get_state.return_value = _state(current_q="Q?")
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.akinetix_service.override(providers.Object(ak)),
    ):
        resp = api_client.post(
            reverse("api_akinetix_answer"), {"answer": "OUI"}, format="json"
        )
    assert resp.status_code == 404
    assert resp.json()["error"] == "Catalog not found"


@pytest.mark.django_db
def test_answer_success(api_client):
    cat = MagicMock()
    cat.load_data.return_value = _CAT
    ak = MagicMock()
    ak.get_state.return_value = _state(current_q="Q?")
    ak.process_answer.return_value = _state(
        current_q="Next?", history=[{"q": "Q?", "a": "OUI"}], game_over=False
    )
    with (
        container.core.catalog_service.override(providers.Object(cat)),
        container.core.akinetix_service.override(providers.Object(ak)),
    ):
        resp = api_client.post(
            reverse("api_akinetix_answer"), {"answer": "OUI"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_question"] == "Next?"
    assert data["history"][0] == {"q": "Q?", "a": "OUI"}
    ak.save_state.assert_called_once()


# --------------------------------------------------------------------------- #
# AkinetixGameConfirmView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_confirm_no_game(api_client):
    ak = MagicMock()
    ak.get_state.return_value = _state(current_q=None, ai_guess=None)
    with container.core.akinetix_service.override(providers.Object(ak)):
        resp = api_client.post(
            reverse("api_akinetix_confirm"), {"correct": True}, format="json"
        )
    assert resp.status_code == 400
    assert resp.json()["error"] == "No game in progress to confirm"


@pytest.mark.django_db
def test_confirm_invalid_serializer(api_client):
    ak = MagicMock()
    ak.get_state.return_value = _state(current_q="Q?", ai_guess="Goku")
    with container.core.akinetix_service.override(providers.Object(ak)):
        resp = api_client.post(reverse("api_akinetix_confirm"), {}, format="json")
    assert resp.status_code == 400
    assert "correct" in resp.json()


@pytest.mark.django_db
def test_confirm_correct_ai_won(api_client):
    """correct=True -> AI guessed right, GameplaySession was_won=True."""
    from animetix.models import GameplaySession

    ak = MagicMock()
    ak.get_state.return_value = _state(
        current_q="Q?", ai_guess="Goku", history=[{"q": "Q?", "a": "OUI"}]
    )
    with container.core.akinetix_service.override(providers.Object(ak)):
        resp = api_client.post(
            reverse("api_akinetix_confirm"), {"correct": True}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "confirmed"
    assert data["was_won"] is True
    assert data["user_won"] is False
    ak.reset_state.assert_called_once()
    assert GameplaySession.objects.filter(target_item="Goku", was_won=True).exists()


@pytest.mark.django_db
def test_confirm_incorrect_missing_actual_target(api_client):
    ak = MagicMock()
    ak.get_state.return_value = _state(current_q="Q?", ai_guess="Goku")
    with container.core.akinetix_service.override(providers.Object(ak)):
        resp = api_client.post(
            reverse("api_akinetix_confirm"),
            {"correct": False},
            format="json",
        )
    assert resp.status_code == 400
    assert "must specify the character" in resp.json()["error"]


@pytest.mark.django_db
def test_confirm_incorrect_cheat_detected(api_client):
    """actual_target equals the AI guess -> cheat detected -> 403."""
    ak = MagicMock()
    ak.get_state.return_value = _state(current_q="Q?", ai_guess="Goku")
    with container.core.akinetix_service.override(providers.Object(ak)):
        resp = api_client.post(
            reverse("api_akinetix_confirm"),
            {"correct": False, "actual_target": "goku"},
            format="json",
        )
    assert resp.status_code == 403
    data = resp.json()
    assert data["is_cheat"] is True


@pytest.mark.django_db
def test_confirm_incorrect_user_won_authenticated(api_client):
    """correct=False with a distinct actual_target -> user won, XP awarded."""
    from animetix.models import GameplaySession

    user = User.objects.create_user("akwin", password="x")
    api_client.force_authenticate(user=user)
    ach = MagicMock()
    ach.name = "Ak Win"
    ach.description = "d"
    ach.xp_reward = 5
    ach.badge_url = "http://b.png"
    user.profile.add_win = MagicMock(return_value=[ach])

    ak = MagicMock()
    ak.get_state.return_value = _state(
        current_q="Q?", ai_guess="Goku", history=[{"q": "Q?", "a": "NON"}]
    )
    with container.core.akinetix_service.override(providers.Object(ak)):
        resp = api_client.post(
            reverse("api_akinetix_confirm"),
            {"correct": False, "actual_target": "Luffy"},
            format="json",
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["was_won"] is False
    assert data["user_won"] is True
    assert data["newly_unlocked_achievements"][0]["name"] == "Ak Win"
    ak.reset_state.assert_called_once()
    assert GameplaySession.objects.filter(target_item="Luffy", was_won=False).exists()


@pytest.mark.django_db
def test_confirm_incorrect_add_win_raises_is_handled(api_client):
    user = User.objects.create_user("akwinerr", password="x")
    api_client.force_authenticate(user=user)
    user.profile.add_win = MagicMock(side_effect=RuntimeError("boom"))

    ak = MagicMock()
    ak.get_state.return_value = _state(current_q="Q?", ai_guess="Goku", history=[])
    with container.core.akinetix_service.override(providers.Object(ak)):
        resp = api_client.post(
            reverse("api_akinetix_confirm"),
            {"correct": False, "actual_target": "Luffy"},
            format="json",
        )
    assert resp.status_code == 200
    assert resp.json()["newly_unlocked_achievements"] == []
