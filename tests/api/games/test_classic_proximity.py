"""Le jeu classique note désormais un RANG, et ne révèle rien sous 50 %."""

from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest
from animetix.containers import container
from core.domain.exceptions import GameLogicError
from dependency_injector import providers
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def _wire():
    import animetix.api.games.classic as classic_mod

    container.wire(modules=[classic_mod])
    yield


@contextmanager
def _proximity(report):
    """Override scoped: une fuite d'override empoisonne toute la session (tripwire)."""
    service = MagicMock()
    # Titres réels du catalogue (data/processed/clean_root_animes.json), casse exacte :
    # la vue vérifie l'appartenance au catalogue avant tout scoring de proximité.
    service.rank.return_value = [
        "MONSTER",
        "Code Geass: Hangyaku no Lelouch",
        "Kimetsu no Yaiba",
    ]
    service.report.return_value = report
    container.core.proximity_service.override(providers.Object(service))
    try:
        yield service
    finally:
        container.core.proximity_service.reset_last_overriding()


HOT_REPORT = {
    "percent": 92.3,
    "rank": 1,
    "total": 3,
    "reasons": [
        {"kind": "public", "label": "C'est le public qui vous rapproche", "detail": []},
        {"kind": "tags", "label": "2 tag(s) partagé(s)", "detail": ["Detective"]},
    ],
}
COLD_REPORT = {"percent": 12.0, "rank": 3, "total": 3, "reasons": []}


def _start(api):
    return api.post(
        "/api/v1/game/classic/start/", {"media_type": "Anime"}, format="json"
    )


@pytest.mark.django_db
def test_a_guess_is_scored_by_its_rank_not_by_a_cosine():
    api = APIClient()
    with _proximity(HOT_REPORT):
        _start(api)
        response = api.post(
            "/api/v1/game/classic/guess/", {"guess": "MONSTER"}, format="json"
        )

    assert response.status_code == 200
    guess = response.json()["guesses"][-1]
    assert guess["score"] == 92.3
    assert [r["kind"] for r in guess["reasons"]] == ["public", "tags"]


@pytest.mark.django_db
def test_a_cold_guess_reveals_nothing():
    api = APIClient()
    with _proximity(COLD_REPORT):
        _start(api)
        response = api.post(
            "/api/v1/game/classic/guess/", {"guess": "Kimetsu no Yaiba"}, format="json"
        )

    guess = response.json()["guesses"][-1]
    assert guess["score"] == 12.0
    assert guess["reasons"] == []


@pytest.mark.django_db
def test_the_ranking_is_computed_once_per_game_not_once_per_guess():
    api = APIClient()
    with _proximity(HOT_REPORT) as service:
        _start(api)
        for title in ("MONSTER", "Code Geass: Hangyaku no Lelouch", "Kimetsu no Yaiba"):
            api.post("/api/v1/game/classic/guess/", {"guess": title}, format="json")

    assert service.rank.call_count == 1


@pytest.mark.django_db
def test_a_media_type_with_no_proximity_signal_is_a_clean_error_not_a_500():
    """Movies, games and actors have no recommendations today: ProximityService.rank
    raises GameLogicError for them (empty index / no exploitable signal). That must
    surface as a clean, well-known status -- never as an unhandled 500."""
    api = APIClient()
    service = MagicMock()
    service.rank.side_effect = GameLogicError("no signal for this catalogue")
    container.core.proximity_service.override(providers.Object(service))
    try:
        response = _start(api)
    finally:
        container.core.proximity_service.reset_last_overriding()

    assert response.status_code == 503
    assert response.status_code != 500
