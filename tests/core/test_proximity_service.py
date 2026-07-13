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


def test_a_genre_only_catalogue_still_produces_a_usable_ranking():
    # La forme "jeu vidéo" du vrai catalogue : ni tags ni recommandations, seulement
    # des genres. Avant le correctif, ce catalogue scorait zéro partout et rank()
    # levait GameLogicError -- une régression : le mode Game était jouable avant.
    games = [
        {
            "title": "Game A",
            "tags": [],
            "genres": ["RPG", "Fantasy"],
            "studios": [],
            "source": None,
            "year": None,
            "relations": {},
            "recommendations": {},
        },
        {
            "title": "Game B",
            "tags": [],
            "genres": ["RPG", "Fantasy"],
            "studios": [],
            "source": None,
            "year": None,
            "relations": {},
            "recommendations": {},
        },
        {
            "title": "Game C",
            "tags": [],
            "genres": ["Shooter"],
            "studios": [],
            "source": None,
            "year": None,
            "relations": {},
            "recommendations": {},
        },
    ] + [
        # Remplit le catalogue pour que RPG/Fantasy restent minoritaires (cf. le
        # commentaire équivalent dans test_proximity_components.py) : sinon leur IDF
        # tombe à zéro et le classement ne prouve plus rien.
        {
            "title": f"Filler{i}",
            "tags": [],
            "genres": [f"Genre{i}"],
            "studios": [],
            "source": None,
            "year": None,
            "relations": {},
            "recommendations": {},
        }
        for i in range(8)
    ]
    ranking = _service(works=games).rank("Game", "Game A")
    assert ranking[0] == "Game B"  # partage les deux genres, contrairement à Game C


def test_a_genre_only_hot_guess_carries_an_honest_tags_reason():
    # Même forme "jeu vidéo" que le test ci-dessus : ni tags, ni recommandations,
    # seulement des genres partagés. La composante vocabulaire (components.tags) score
    # sur tags UNION genres -- mais _reasons, avant ce correctif, ne relisait QUE le
    # champ "tags" des œuvres pour bâtir le label et le detail. Résultat : pour Game B,
    # le service affichait "0 tag(s) partagé(s)" avec un detail vide, alors que le score
    # HOT affiché au joueur est intégralement porté par RPG/Fantasy partagés -- un
    # mensonge. Ce test épingle qu'après correctif, la raison "tags" nomme bien le
    # genre partagé.
    games = [
        {
            "title": "Game A",
            "tags": [],
            "genres": ["RPG", "Fantasy"],
            "studios": [],
            "source": None,
            "year": None,
            "relations": {},
            "recommendations": {},
        },
        {
            "title": "Game B",
            "tags": [],
            "genres": ["RPG", "Fantasy"],
            "studios": [],
            "source": None,
            "year": None,
            "relations": {},
            "recommendations": {},
        },
        {
            "title": "Game C",
            "tags": [],
            "genres": ["Shooter"],
            "studios": [],
            "source": None,
            "year": None,
            "relations": {},
            "recommendations": {},
        },
    ] + [
        {
            "title": f"Filler{i}",
            "tags": [],
            "genres": [f"Genre{i}"],
            "studios": [],
            "source": None,
            "year": None,
            "relations": {},
            "recommendations": {},
        }
        for i in range(8)
    ]
    report = _service(works=games).report("Game", "Game A", "Game B")
    assert report["percent"] >= 80

    tags_reason = next((r for r in report["reasons"] if r["kind"] == "tags"), None)
    assert tags_reason is not None
    # Le cœur du correctif : le detail ne doit pas être vide, et doit nommer le
    # genre réellement partagé -- pas un tag inexistant.
    assert tags_reason["detail"]
    assert "RPG" in tags_reason["detail"] or "Fantasy" in tags_reason["detail"]
    # La formulation d'origine ("0 tag(s) partagé(s)") était un mensonge pur et simple
    # ici : elle ne doit plus apparaître.
    assert "0 tag" not in tags_reason["label"]


def test_a_character_shaped_catalogue_ranks_without_raising_and_shared_origin_wins():
    # Forme "personnage" du vrai catalogue (data/processed/filtered_characters.json) :
    # ni tags, ni genres, ni recommandations -- seulement origin/traits/
    # entities.organizations. Avant le correctif de l'IMPORTANT 1, ce catalogue
    # scorait zéro partout et rank() levait GameLogicError : le mode Personnages
    # était injouable alors que c'est l'un des trois univers proposés en lobby.
    characters = [
        {
            "name": "Levi",
            "origin": "Shingeki no Kyojin",
            "traits": [],
            "entities": {"organizations": ["Survey Corps"]},
        },
        {
            "name": "Erwin",
            "origin": "Shingeki no Kyojin",
            "traits": [],
            "entities": {"organizations": ["Survey Corps"]},
        },
    ] + [
        # Des inconnus d'œuvres et organisations toutes différentes : aucun ne
        # doit dépasser Erwin, qui partage l'origine ET l'organisation avec Levi.
        {
            "name": f"Stranger{i}",
            "origin": f"Show {i}",
            "traits": [],
            "entities": {"organizations": [f"Org{i}"]},
        }
        for i in range(8)
    ]
    ranking = _service(works=characters).rank("Character", "Levi")
    assert ranking[0] == "Erwin"


def test_an_actor_shape_catalogue_with_no_signal_at_all_still_raises():
    # La forme "acteur" du vrai catalogue : ni tags, ni genres, ni recommandations.
    # Là, aucun vocabulaire fusionné ne peut aider -- GameLogicError reste la bonne
    # réponse : un 0.0 qui a l'air d'un vrai chiffre est le bug que cette refonte tue.
    actors = [
        {
            "title": "Actor A",
            "tags": [],
            "genres": [],
            "studios": [],
            "source": None,
            "year": None,
            "relations": {},
            "recommendations": {},
        },
        {
            "title": "Actor B",
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
        _service(works=actors).rank("Actor", "Actor A")


def test_the_ranking_can_be_passed_in_so_a_game_computes_it_once():
    service = _service()
    ranking = service.rank("Anime", "Death Note")
    report = service.report("Anime", "Death Note", "Monster", ranking=ranking)
    assert (
        report["percent"] == service.report("Anime", "Death Note", "Monster")["percent"]
    )
