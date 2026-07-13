"""Le jeu classique note désormais un RANG, et ne révèle rien sous 50 %."""

from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest
from animetix.containers import container
from core.domain.exceptions import GameLogicError
from dependency_injector import providers
from django.core.cache import cache
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


# CI checks out data/processed/*.json as unfetched Git LFS pointers (~130-byte
# stubs starting with "version https://git-lfs...") -- the real CatalogService
# raises CatalogNotFoundError for every media type there. None of these tests
# exercise real catalogue data or secret-selection logic (scoring is faked via
# ``_proximity`` above); they only need the view's own membership/display-field
# checks and a fixed secret title. A tiny in-memory catalogue -- same shape
# CatalogService.get_catalog produces, same pattern as
# tests/api/games/test_classic_coverage.py's ``mock_catalog`` -- stands in.
SECRET_TITLE = "Placeholder Secret"


def _catalog():
    titles = [
        "MONSTER",
        "Code Geass: Hangyaku no Lelouch",
        "Kimetsu no Yaiba",
        SECRET_TITLE,
    ]
    return {
        "title_to_full_data": {t: {"title": t} for t in titles},
        "titles": titles,
        "title_to_index": {t: i for i, t in enumerate(titles)},
        "lookup": [{"id": i, "title": t} for i, t in enumerate(titles)],
        "db": [{"id": i, "title": t} for i, t in enumerate(titles)],
    }


@contextmanager
def _catalog_and_game(secret_title=SECRET_TITLE):
    """Override scoped, same tripwire discipline as ``_proximity`` above."""
    cat = MagicMock()
    cat.get_catalog.return_value = _catalog()
    game = MagicMock()
    game.select_secret.return_value = secret_title
    # Never let a guess collide with the secret by accident (check_title_match
    # unconfigured on a MagicMock returns a truthy MagicMock, which would score
    # every guess 100.0 and break every assertion below that pins the mocked
    # ProximityService report instead).
    game.check_title_match.return_value = False
    container.core.catalog_service.override(providers.Object(cat))
    container.core.game_service.override(providers.Object(game))
    try:
        yield cat, game
    finally:
        container.core.game_service.reset_last_overriding()
        container.core.catalog_service.reset_last_overriding()


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
    with _catalog_and_game(), _proximity(HOT_REPORT):
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
    with _catalog_and_game(), _proximity(COLD_REPORT):
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
    with _catalog_and_game(), _proximity(HOT_REPORT) as service:
        _start(api)
        for title in ("MONSTER", "Code Geass: Hangyaku no Lelouch", "Kimetsu no Yaiba"):
            api.post("/api/v1/game/classic/guess/", {"guess": title}, format="json")

    assert service.rank.call_count == 1


@pytest.mark.django_db
def test_a_stale_v1_session_key_does_not_recompute_every_guess():
    """Une session ouverte avant le passage au cache v2 porte encore une clé v1
    (``proximity_{media}_{secret}``, sans le ``_v2_``) ; ces entrées vivent
    encore 7 jours. Cette clé HIT le cache -- mais son contenu (des titres nus,
    sans score) est un format que ``ProximityService._as_ranking`` refuse, à
    raison, de croire sur parole : il recalcule. Comme la vue ne remet en cache
    QUE sur un ``None``, une clé de session non-v2 ferait recalculer à CHAQUE
    proposition pour le reste de la partie -- sur le catalogue Personnages
    (32 384 entrées), un recalcul complet par proposition. Ce test simule
    exactement cette session : on rejoue la clé v1 et l'entrée nue qu'un
    déploiement antérieur y aurait laissée, et on vérifie que le classement
    n'est recalculé qu'une fois, pas à chaque proposition.
    """
    api = APIClient()
    service = MagicMock()
    # Le VRAI rank() v2 rend des paires (titre, score) -- la vue ne doit jamais
    # relire une entrée v1 (des titres nus) sans la juger périmée.
    tuple_ranking = [
        ("MONSTER", 92.3),
        ("Code Geass: Hangyaku no Lelouch", 50.0),
        ("Kimetsu no Yaiba", 12.0),
    ]
    service.rank.return_value = tuple_ranking

    def fake_report(media_type, secret_title, guess_title, ranking=None):
        # Mirroir de ProximityService._as_ranking : un classement nu (pas de
        # paires) est un format d'une version antérieure -- on le rejette et on
        # recalcule, exactement comme le service réel.
        stale_format = not ranking or not isinstance(ranking[0], (list, tuple))
        if stale_format:
            service.rank(media_type, secret_title)
        return HOT_REPORT

    service.report.side_effect = fake_report

    with (
        _catalog_and_game(),
        container.core.proximity_service.override(providers.Object(service)),
    ):
        _start(api)

        session = api.session
        secret_title = session["secret_title"]
        media_type = session["media_type"]

        # Simule l'entrée v1 qu'un déploiement antérieur aurait laissée en
        # cache (le VRAI cache Django, pas le mock) -- toujours vivante, sept
        # jours de TTL obligent -- et une session qui pointe encore dessus.
        v1_key = f"proximity_{media_type}_{secret_title}"
        cache.set(
            v1_key, ["MONSTER", "Code Geass: Hangyaku no Lelouch", "Kimetsu no Yaiba"]
        )
        session["proximity_key"] = v1_key
        session.save()

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
    with _catalog_and_game():
        container.core.proximity_service.override(providers.Object(service))
        try:
            response = _start(api)
        finally:
            container.core.proximity_service.reset_last_overriding()

    assert response.status_code == 503
    assert response.status_code != 500
