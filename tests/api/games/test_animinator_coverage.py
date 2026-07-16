"""Coverage tests for ``animetix.api.games.animinator`` (solo Animinator oracle
HTTP API: ask + guess).

The async SSE variant (``AniminatorStreamView`` in streams.py) is covered by
tests/api/test_animinator_stream_view.py — nothing here drives it. These tests
exercise the two synchronous DRF views end-to-end through the real Django
session. ``animinator_service`` / ``catalog_service`` are replaced with
instance-level container overrides; ``deduct_berrix`` is patched at the module
namespace so the GPU-turn charge doesn't need a seeded wallet (one test lets it
raise to prove the 402 is not swallowed into a 500).
"""

from unittest.mock import MagicMock, patch

import animetix.api.games.animinator as animinator_mod
import pytest
from animetix.api.billing import PaymentRequired
from animetix.containers import container
from animetix.models import GameplaySession
from dependency_injector import providers
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def _wire_animinator():
    container.wire(modules=[animinator_mod])
    yield


@pytest.fixture
def auth_client(db):
    user = User.objects.create_user(username="oracle-player", password="pw")
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _oracle_service():
    svc = MagicMock()
    svc.ask_oracle_stream.return_value = iter(["Il ", "est ", "un ninja."])
    return svc


def _catalog_service(data):
    cs = MagicMock()
    cs.load_data.return_value = data
    return cs


def _catalog_data():
    return {
        "lookup": [{"title": "Naruto"}, {"title": "Luffy"}],
        "title_to_full_data": {"Naruto": {}, "Luffy": {}},
    }


def _override_core(**services):
    return [
        getattr(container.core, name).override(providers.Object(svc))
        for name, svc in services.items()
    ]


def _seed_ask_session(client, secret="Naruto", questions_left=20, chat=None):
    session = client.session
    session["animinator_secret"] = secret
    session["animinator_questions_left"] = questions_left
    session["animinator_chat"] = chat if chat is not None else []
    session["media_type"] = "Anime"
    session.save()


# --------------------------------------------------------------------------- #
# AniminatorAskView (IsAuthenticated, consumes Berrix)
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_ask_requires_authentication(api_client):
    resp = api_client.post(
        reverse("api_animinator_ask"), {"question": "?"}, format="json"
    )
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_ask_missing_question_returns_400(auth_client):
    resp = auth_client.post(reverse("api_animinator_ask"), {}, format="json")
    assert resp.status_code == 400
    assert resp.json()["error"] == "No question provided."


@pytest.mark.django_db
def test_ask_new_game_catalog_not_found_returns_404(auth_client):
    cat = _catalog_service(None)
    _override_core(catalog_service=cat, animinator_service=_oracle_service())
    try:
        with patch.object(animinator_mod, "deduct_berrix"):
            resp = auth_client.post(
                reverse("api_animinator_ask"), {"question": "ninja?"}, format="json"
            )
    finally:
        container.core.catalog_service.reset_last_overriding()
        container.core.animinator_service.reset_last_overriding()
    assert resp.status_code == 404
    assert resp.json()["error"] == "Catalog not found"


@pytest.mark.django_db
def test_ask_new_game_seeds_secret_and_returns_answer(auth_client):
    cat = _catalog_service(_catalog_data())
    oracle = _oracle_service()
    _override_core(catalog_service=cat, animinator_service=oracle)
    try:
        with patch.object(animinator_mod, "deduct_berrix") as deduct:
            resp = auth_client.post(
                reverse("api_animinator_ask"),
                {"question": "Est-ce un ninja ?", "media_type": "Anime"},
                format="json",
            )
    finally:
        container.core.catalog_service.reset_last_overriding()
        container.core.animinator_service.reset_last_overriding()

    assert resp.status_code == 200
    body = resp.json()
    # Streamed tokens are joined and HTML-sanitized.
    assert body["answer"] == "Il est un ninja."
    assert body["questions_left"] == 19
    deduct.assert_called_once()
    # A secret was chosen from the catalog pool and stored in the session.
    assert auth_client.session["animinator_secret"] in ("Naruto", "Luffy")
    oracle.ask_oracle_stream.assert_called_once()


@pytest.mark.django_db
def test_ask_last_question_ends_game_and_records_loss(auth_client):
    _seed_ask_session(auth_client, secret="Naruto", questions_left=1)
    oracle = _oracle_service()
    _override_core(
        catalog_service=_catalog_service(_catalog_data()), animinator_service=oracle
    )
    try:
        with patch.object(animinator_mod, "deduct_berrix"):
            resp = auth_client.post(
                reverse("api_animinator_ask"), {"question": "dernier ?"}, format="json"
            )
    finally:
        container.core.catalog_service.reset_last_overriding()
        container.core.animinator_service.reset_last_overriding()

    assert resp.status_code == 200
    assert resp.json()["questions_left"] == 0
    lost = GameplaySession.objects.filter(game_mode="animinator", was_won=False)
    assert lost.exists()
    assert auth_client.session.get("animinator_game_over") is True


@pytest.mark.django_db
def test_ask_insufficient_berrix_returns_402_not_500(auth_client):
    _seed_ask_session(auth_client, secret="Naruto")
    _override_core(
        catalog_service=_catalog_service(_catalog_data()),
        animinator_service=_oracle_service(),
    )
    try:
        with patch.object(
            animinator_mod, "deduct_berrix", side_effect=PaymentRequired()
        ):
            resp = auth_client.post(
                reverse("api_animinator_ask"), {"question": "ninja?"}, format="json"
            )
    finally:
        container.core.catalog_service.reset_last_overriding()
        container.core.animinator_service.reset_last_overriding()
    # PaymentRequired is raised OUTSIDE the try/except, so it surfaces as 402
    # rather than being swallowed into a generic 500.
    assert resp.status_code == 402


@pytest.mark.django_db
def test_ask_oracle_failure_returns_500(auth_client):
    _seed_ask_session(auth_client, secret="Naruto")
    oracle = MagicMock()
    oracle.ask_oracle_stream.side_effect = RuntimeError("oracle down")
    _override_core(
        catalog_service=_catalog_service(_catalog_data()), animinator_service=oracle
    )
    try:
        with patch.object(animinator_mod, "deduct_berrix"):
            resp = auth_client.post(
                reverse("api_animinator_ask"), {"question": "ninja?"}, format="json"
            )
    finally:
        container.core.catalog_service.reset_last_overriding()
        container.core.animinator_service.reset_last_overriding()
    assert resp.status_code == 500
    assert resp.json()["error"] == "Internal server error"


# --------------------------------------------------------------------------- #
# AniminatorGuessView (AllowAny, CPU comparison)
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_guess_no_game_in_progress_returns_400(api_client):
    resp = api_client.post(
        reverse("api_animinator_guess"), {"guess": "Naruto"}, format="json"
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "No game in progress"


@pytest.mark.django_db
def test_guess_missing_guess_returns_400(api_client):
    _seed_ask_session(api_client, secret="Naruto")
    _override_core(animinator_service=_oracle_service())
    try:
        resp = api_client.post(reverse("api_animinator_guess"), {}, format="json")
    finally:
        container.core.animinator_service.reset_last_overriding()
    assert resp.status_code == 400
    assert resp.json()["error"] == "guess is required"


@pytest.mark.django_db
def test_guess_correct_ends_game_and_reveals_secret(auth_client):
    _seed_ask_session(auth_client, secret="Naruto", chat=[{"q": "a", "a": "b"}])
    oracle = MagicMock()
    oracle.check_guess.return_value = True
    _override_core(animinator_service=oracle)
    try:
        resp = auth_client.post(
            reverse("api_animinator_guess"), {"guess": "Naruto"}, format="json"
        )
    finally:
        container.core.animinator_service.reset_last_overriding()

    body = resp.json()
    assert body["correct"] is True
    assert body["game_over"] is True
    assert body["secret"] == "Naruto"
    assert GameplaySession.objects.filter(game_mode="animinator", was_won=True).exists()
    # Secret cleared for replay.
    assert auth_client.session["animinator_secret"] == ""


@pytest.mark.django_db
def test_guess_wrong_keeps_secret_hidden(api_client):
    _seed_ask_session(api_client, secret="Naruto")
    oracle = MagicMock()
    oracle.check_guess.return_value = False
    _override_core(animinator_service=oracle)
    try:
        resp = api_client.post(
            reverse("api_animinator_guess"), {"guess": "Luffy"}, format="json"
        )
    finally:
        container.core.animinator_service.reset_last_overriding()

    body = resp.json()
    assert body["correct"] is False
    assert body["game_over"] is False
    assert body["secret"] is None
