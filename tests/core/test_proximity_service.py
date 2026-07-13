"""Le classement et les explications bridées.

Le joueur lit un RANG, pas un score : « 30e sur 2181 » -> 98,6 %. C'est le seul
moyen de toujours pouvoir chauffer, y compris sur un secret obscur -- ce qui manque
aujourd'hui, où le plancher de bruit de l'embedding (0,583) écrase l'échelle.
"""

from unittest.mock import MagicMock

import pytest
from core.domain.exceptions import GameLogicError
from core.domain.services.proximity.service import ProximityService

from tests.core.test_proximity_components import WORKS


def _service(works=None):
    catalog = MagicMock()
    catalog.load_data.return_value = {"db": list(works if works is not None else WORKS)}
    return ProximityService(catalog_service=catalog)


def test_the_ranking_puts_the_real_neighbour_first():
    ranking = _service().rank("Anime", "Death Note")
    assert ranking[0] in ("Monster", "Code Geass")
    assert ranking.index("Monster") < ranking.index("Kimetsu no Yaiba")


def test_the_secret_itself_is_not_in_the_ranking():
    assert "Death Note" not in _service().rank("Anime", "Death Note")


def test_a_close_guess_scores_high_and_a_stranger_scores_low():
    service = _service()
    close = service.report("Anime", "Death Note", "Monster")
    far = service.report("Anime", "Death Note", "Kimetsu no Yaiba")

    assert close["percent"] > 80
    assert far["percent"] < 50
    assert close["rank"] < far["rank"]
    assert close["total"] == len(WORKS) - 1  # tout le catalogue sauf le secret


def test_a_cold_guess_carries_no_reason_at_all():
    # Sous 50 %, la charge utile ne doit RIEN apprendre : sinon éliminer devient aussi
    # rentable que chercher. Vérifié sur la charge utile, pas sur l'affichage.
    far = _service().report("Anime", "Death Note", "Kimetsu no Yaiba")
    assert far["reasons"] == []


def test_a_warm_guess_carries_exactly_one_reason():
    warm = _service().report("Anime", "Death Note", "Psycho-Pass")
    assert 50 <= warm["percent"] < 80
    assert len(warm["reasons"]) == 1


def test_a_hot_guess_carries_two_reasons_with_their_content():
    hot = _service().report("Anime", "Death Note", "Monster")
    assert hot["percent"] >= 80
    assert len(hot["reasons"]) == 2
    tags = next((r for r in hot["reasons"] if r["kind"] == "tags"), None)
    assert tags and "Detective" in tags["detail"]


def test_the_structural_bonus_is_never_shown_alone():
    for guess in ("Monster", "Psycho-Pass", "Code Geass", "Kimetsu no Yaiba"):
        reasons = _service().report("Anime", "Death Note", guess)["reasons"]
        if reasons:
            assert reasons[0]["kind"] != "structure"


def test_a_media_type_with_no_signal_says_so_instead_of_returning_zero():
    # Le piège dans lequel ce jeu est tombé : un 0.0 qui a l'air d'un vrai chiffre.
    with pytest.raises(GameLogicError):
        _service(works=[]).rank("Movie", "Whatever")


def test_a_catalogue_with_works_but_no_usable_signal_also_says_so():
    # Des œuvres existent, mais aucune recommandation ni tag partagé : un classement
    # serait arbitraire. Le service le DIT plutôt que de rendre un ordre inventé.
    mute = [
        {
            "title": "A",
            "tags": [],
            "genres": [],
            "studios": [],
            "source": None,
            "year": None,
            "relations": {},
            "recommendations": {},
        },
        {
            "title": "B",
            "tags": [],
            "genres": [],
            "studios": [],
            "source": None,
            "year": None,
            "relations": {},
            "recommendations": {},
        },
    ]
    with pytest.raises(GameLogicError):
        _service(works=mute).rank("Movie", "A")


def test_the_ranking_can_be_passed_in_so_a_game_computes_it_once():
    service = _service()
    ranking = service.rank("Anime", "Death Note")
    report = service.report("Anime", "Death Note", "Monster", ranking=ranking)
    assert (
        report["percent"] == service.report("Anime", "Death Note", "Monster")["percent"]
    )
