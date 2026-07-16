"""Coverage tests for ``animetix.api.games.quiz_who`` (solo 'Qui est-ce ?' HTTP API).

Exercises the start / ask / guess endpoints end-to-end through the real Django
session (the views keep their whole game state in ``request.session`` behind
the session-state port, prefixed ``quizwho_``). The DI ``catalog_service`` /
``akinetix_service`` providers are replaced with instance-level container
overrides; the Akinetix engine is a deterministic fake whose attribute checks
read an ``attrs`` list carried by each catalog item (same fake as the consumer
tests).

Scope guard: the real-time duel (``QuizWhoConsumer``) is covered by
``tests/api/test_quizwho_consumer.py`` — nothing here drives the consumer.
Views are AllowAny (CPU game) so most tests run anonymously; the profile-win
branch authenticates a real user.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock

import animetix.api.games.quiz_who as quiz_who_mod
import pytest
from animetix.containers import container
from animetix.models import GameplaySession
from dependency_injector import providers
from django.contrib.auth.models import User
from django.urls import reverse


@pytest.fixture(autouse=True)
def _wire_quiz_who():
    """Bind the @inject markers of the quiz_who module to the live container.

    The shared games conftest re-wires the other game view modules each test but
    does not know about quiz_who; without this the ``Provide[...]`` defaults stay
    stale and per-test overrides would not be seen by the views.
    """
    container.wire(modules=[quiz_who_mod])
    yield


# --------------------------------------------------------------------------- #
# Deterministic Akinetix-engine fake + catalog data
# --------------------------------------------------------------------------- #
class _Formatter:
    def format(self, at):
        return f"est {at}"


class _FakeEngine:
    formatter = _Formatter()

    def _item_attribute_set(self, item, fine):
        return set(item.get("attrs", []))

    def _check_attribute_instance(self, item, attr, fine):
        return attr in item.get("attrs", [])


def _fake_db(n=16):
    """n items: all share 'commun'; the first half are 'fille'; evens 'magie'."""
    db = []
    for i in range(n):
        attrs = ["commun"]
        if i < n // 2:
            attrs.append("fille")
        if i % 2 == 0:
            attrs.append("magie")
        db.append(
            {"id": str(i), "title": f"C{i}", "image": f"i{i}.png", "attrs": attrs}
        )
    return db


def _catalog(db=None):
    db = _fake_db() if db is None else db
    return {"db": db, "id_to_full_data": {it["id"]: it for it in db}}


def _cat_service(catalog):
    cs = MagicMock()
    cs.load_data.return_value = catalog
    cs.get_akinetix_attributes.return_value = {}
    return cs


def _ak_service():
    ak = MagicMock()
    ak.engine = _FakeEngine()
    return ak


@contextmanager
def _overrides(cat, ak):
    """Override both providers for the block, then restore BOTH.

    This used to return the two OverridingContexts, and call sites did
    ``with _overrides(...)[0], _overrides(...)[1]:`` — which calls the helper
    twice (applying four overrides) while exiting only one context each. Two
    MagicMocks leaked onto the container per test. A leaked ``catalog_service``
    mock then reached unrelated suites (tests/api/test_explore.py), where DRF's
    JSON encoder hangs forever on a MagicMock: it calls ``obj.tolist()``, gets
    another MagicMock, and tries to encode that one too. CI died on it (SIGTERM).
    """
    container.core.catalog_service.override(providers.Object(cat))
    container.core.akinetix_service.override(providers.Object(ak))
    try:
        yield
    finally:
        container.core.catalog_service.reset_last_overriding()
        container.core.akinetix_service.reset_last_overriding()


def _seed_game(
    api_client,
    secret="0",
    board=None,
    eliminated=None,
    asked=None,
    over=False,
    media_type="Anime",
):
    """Seed a quiz-who game directly into the session (keys the views read)."""
    session = api_client.session
    session.update(
        {
            "quizwho_secret": secret,
            "quizwho_board": (
                board if board is not None else [str(i) for i in range(16)]
            ),
            "quizwho_eliminated": eliminated if eliminated is not None else [],
            "quizwho_asked": asked if asked is not None else [],
            "quizwho_over": over,
            "quizwho_media_type": media_type,
        }
    )
    session.save()


# --------------------------------------------------------------------------- #
# QuiEstCeStartView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_start_catalog_not_found(api_client):
    cat = _cat_service(None)
    with _overrides(cat, _ak_service()):
        resp = api_client.post(reverse("api_quiz_who_start"), {}, format="json")
    assert resp.status_code == 404
    assert resp.json()["error"] == "Catalog not found"


@pytest.mark.django_db
def test_start_not_enough_candidates_with_images(api_client):
    # Only 3 of 10 items have an image -> pool < 4 -> refuse to build a board.
    db = [
        {"id": str(i), "title": f"C{i}", "image": f"i{i}.png" if i < 3 else None}
        for i in range(10)
    ]
    cat = _cat_service(_catalog(db))
    ak = _ak_service()
    with _overrides(cat, ak):
        resp = api_client.post(reverse("api_quiz_who_start"), {}, format="json")
    assert resp.status_code == 400
    assert "Not enough candidates" in resp.json()["error"]


@pytest.mark.django_db
def test_start_builds_board_and_stores_secret_in_session(api_client):
    cat = _cat_service(_catalog())
    ak = _ak_service()
    with _overrides(cat, ak):
        resp = api_client.post(
            reverse("api_quiz_who_start"),
            {"media_type": "Manga", "difficulty": "Easy"},
            format="json",
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["media_type"] == "Manga"
    assert data["asked_count"] == 0
    assert data["game_over"] is False
    assert len(data["board"]) == 16
    for card in data["board"]:
        assert card["id"] and card["title"].startswith("C") and card["image"]
    cat.load_data.assert_called_once_with("Manga")
    session = api_client.session
    board_ids = [c["id"] for c in data["board"]]
    assert session["quizwho_secret"] in board_ids  # secret hidden but on-board
    assert session["quizwho_board"] == board_ids
    assert session["quizwho_over"] is False
    assert session["quizwho_media_type"] == "Manga"


@pytest.mark.django_db
def test_start_offers_only_discriminating_attributes(api_client):
    cat = _cat_service(_catalog())
    ak = _ak_service()
    with _overrides(cat, ak):
        resp = api_client.post(reverse("api_quiz_who_start"), {}, format="json")
    assert resp.status_code == 200
    questions = resp.json()["questions"]
    attrs = {q["attr"] for q in questions}
    # 'commun' is carried by every board item -> useless, never offered.
    assert "commun" not in attrs
    # 'fille' / 'magie' each split the 16-item board in half -> best questions.
    assert {"fille", "magie"} <= attrs
    labels = [q["label"] for q in questions]
    assert labels and len(labels) == len(set(labels))  # labels deduplicated


# --------------------------------------------------------------------------- #
# QuiEstCeAskView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_ask_without_game_in_progress(api_client):
    cat = _cat_service(_catalog())
    ak = _ak_service()
    with _overrides(cat, ak):
        resp = api_client.post(
            reverse("api_quiz_who_ask"), {"attribute": "fille"}, format="json"
        )
    assert resp.status_code == 400
    assert resp.json()["error"] == "No game in progress"


@pytest.mark.django_db
def test_ask_missing_attribute(api_client):
    _seed_game(api_client)
    cat = _cat_service(_catalog())
    ak = _ak_service()
    with _overrides(cat, ak):
        resp = api_client.post(reverse("api_quiz_who_ask"), {}, format="json")
    assert resp.status_code == 400
    assert resp.json()["error"] == "attribute is required"


@pytest.mark.django_db
def test_ask_catalog_not_found(api_client):
    _seed_game(api_client)
    cat = _cat_service(None)
    ak = _ak_service()
    with _overrides(cat, ak):
        resp = api_client.post(
            reverse("api_quiz_who_ask"), {"attribute": "fille"}, format="json"
        )
    assert resp.status_code == 404
    assert resp.json()["error"] == "Catalog not found"


@pytest.mark.django_db
def test_ask_secret_missing_from_catalog(api_client):
    # A stale session secret that the (reloaded) catalog no longer contains.
    _seed_game(api_client, secret="999")
    cat = _cat_service(_catalog())
    ak = _ak_service()
    with _overrides(cat, ak):
        resp = api_client.post(
            reverse("api_quiz_who_ask"), {"attribute": "fille"}, format="json"
        )
    assert resp.status_code == 400
    assert resp.json()["error"] == "Secret unavailable"


@pytest.mark.django_db
def test_ask_oui_eliminates_non_matching_candidates(api_client):
    # Secret item 0 IS 'fille' -> answer OUI, the 8 non-'fille' items drop.
    _seed_game(api_client, secret="0")
    cat = _cat_service(_catalog())
    ak = _ak_service()
    with _overrides(cat, ak):
        resp = api_client.post(
            reverse("api_quiz_who_ask"), {"attribute": "fille"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "OUI"
    assert set(data["eliminated"]) == {str(i) for i in range(8, 16)}
    assert data["remaining_count"] == 8
    assert data["asked_count"] == 1
    assert api_client.session["quizwho_asked"] == ["fille"]


@pytest.mark.django_db
def test_ask_non_eliminates_matching_candidates(api_client):
    # Secret item 1 is NOT 'magie' -> answer NON, the 8 'magie' items drop.
    _seed_game(api_client, secret="1")
    cat = _cat_service(_catalog())
    ak = _ak_service()
    with _overrides(cat, ak):
        resp = api_client.post(
            reverse("api_quiz_who_ask"), {"attribute": "magie"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "NON"
    assert set(data["eliminated"]) == {str(i) for i in range(0, 16, 2)}
    assert data["remaining_count"] == 8


@pytest.mark.django_db
def test_ask_does_not_re_report_already_eliminated(api_client):
    # '8' was already crossed off -> it must not reappear in 'eliminated'.
    _seed_game(api_client, secret="0", eliminated=["8"])
    cat = _cat_service(_catalog())
    ak = _ak_service()
    with _overrides(cat, ak):
        resp = api_client.post(
            reverse("api_quiz_who_ask"), {"attribute": "fille"}, format="json"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert set(data["eliminated"]) == {str(i) for i in range(9, 16)}
    assert data["remaining_count"] == 8  # '8' still counted as eliminated


# --------------------------------------------------------------------------- #
# QuiEstCeGuessView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_guess_without_game_in_progress(api_client):
    cat = _cat_service(_catalog())
    with container.core.catalog_service.override(providers.Object(cat)):
        resp = api_client.post(
            reverse("api_quiz_who_guess"), {"guess_id": "3"}, format="json"
        )
    assert resp.status_code == 400
    assert resp.json()["error"] == "No game in progress"


@pytest.mark.django_db
def test_guess_correct_ends_game_records_session_and_blocks_further_asks(api_client):
    _seed_game(api_client, secret="3", asked=["fille", "magie"])
    cat = _cat_service(_catalog())
    ak = _ak_service()
    with _overrides(cat, ak):
        resp = api_client.post(
            reverse("api_quiz_who_guess"), {"guess_id": "3"}, format="json"
        )
        assert resp.status_code == 200
        assert resp.json() == {
            "correct": True,
            "game_over": True,
            "secret_title": "C3",
        }
        gs = GameplaySession.objects.get(game_mode="quiz_who")
        assert gs.user is None  # anonymous player
        assert gs.was_won is True
        assert gs.target_item == "C3"
        assert gs.history == [{"asked": ["fille", "magie"]}]
        # The finished game refuses further questions (quizwho_over flag).
        resp2 = api_client.post(
            reverse("api_quiz_who_ask"), {"attribute": "fille"}, format="json"
        )
        assert resp2.status_code == 400
        assert resp2.json()["error"] == "No game in progress"


@pytest.mark.django_db
def test_guess_correct_authenticated_records_profile_win(api_client):
    user = User.objects.create_user("qwwin", password="x")
    api_client.force_authenticate(user=user)
    user.profile.add_win = MagicMock(return_value=[])
    _seed_game(api_client, secret="3", asked=["fille"])
    cat = _cat_service(_catalog())
    ak = _ak_service()
    with _overrides(cat, ak):
        resp = api_client.post(
            reverse("api_quiz_who_guess"), {"guess_id": "3"}, format="json"
        )
    assert resp.status_code == 200
    assert resp.json()["correct"] is True
    user.profile.add_win.assert_called_once_with(
        game_mode="quiz_who", media_type="Anime", attempts=1
    )
    assert GameplaySession.objects.filter(
        game_mode="quiz_who", user=user, was_won=True
    ).exists()


@pytest.mark.django_db
def test_guess_correct_add_win_error_is_handled(api_client):
    user = User.objects.create_user("qwwinerr", password="x")
    api_client.force_authenticate(user=user)
    user.profile.add_win = MagicMock(side_effect=RuntimeError("boom"))
    _seed_game(api_client, secret="3")
    cat = _cat_service(_catalog())
    ak = _ak_service()
    with _overrides(cat, ak):
        resp = api_client.post(
            reverse("api_quiz_who_guess"), {"guess_id": "3"}, format="json"
        )
    assert resp.status_code == 200  # profile failure never breaks the win
    assert resp.json()["correct"] is True
    assert GameplaySession.objects.filter(game_mode="quiz_who", was_won=True).exists()


@pytest.mark.django_db
def test_guess_wrong_flips_tile_and_game_continues(api_client):
    _seed_game(api_client, secret="3")
    cat = _cat_service(_catalog())
    ak = _ak_service()
    with _overrides(cat, ak):
        resp = api_client.post(
            reverse("api_quiz_who_guess"), {"guess_id": "5"}, format="json"
        )
    assert resp.status_code == 200
    assert resp.json() == {"correct": False, "game_over": False, "eliminated": ["5"]}
    assert "5" in api_client.session["quizwho_eliminated"]
    assert api_client.session["quizwho_over"] is False
    assert not GameplaySession.objects.filter(game_mode="quiz_who").exists()
