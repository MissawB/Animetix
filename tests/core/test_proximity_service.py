"""Le classement et les explications bridées.

Le joueur lit un RANG, pas un score : « 30e sur 2181 » -> 98,6 %. C'est le seul
moyen de toujours pouvoir chauffer, y compris sur un secret obscur -- ce qui manque
aujourd'hui, où le plancher de bruit de l'embedding (0,583) écrase l'échelle.
"""

from unittest.mock import MagicMock

import pytest
from core.domain.exceptions import GameLogicError
from core.domain.services.proximity.components import build_index, score
from core.domain.services.proximity.service import (
    HOT_FLOOR,
    WARM_FLOOR,
    ProximityService,
)

from tests.core.test_proximity_components import WORKS


def _service(works=None):
    catalog = MagicMock()
    catalog.load_data.return_value = {"db": list(works if works is not None else WORKS)}
    return ProximityService(catalog_service=catalog)


def _work(title, **kwargs):
    base = {
        "title": title,
        "tags": [],
        "genres": [],
        "studios": [],
        "source": None,
        "year": None,
        "relations": {},
        "recommendations": {},
    }
    base.update(kwargs)
    return base


def _one_signal_catalogue(extra=()):
    """Un secret, un vrai voisin, et une longue traîne d'œuvres SANS AUCUN signal.

    C'est la forme du vrai catalogue personnages : face à Levi, 104 personnages
    scorent non nul et 32 280 scorent exactement 0. Les noms des figurants
    encadrent alphabétiquement le reste : c'est ce qui trahissait le percentile
    calculé sur une position d'index.
    """
    return (
        [
            _work("Secret", recommendations={"Neighbour": 3000}),
            _work("Neighbour", recommendations={"Secret": 3000}),
        ]
        + list(extra)
        + [_work(f"Filler {i}") for i in range(10)]
    )


def _titles(ranking):
    """Le classement porte désormais (titre, score) : le score EST le classement.

    Sans lui, report() ne peut compter que des positions d'index -- et c'est
    exactement le bug que le CRITIQUE 1 corrige.
    """
    return [title for title, _ in ranking]


def test_the_ranking_puts_the_real_neighbour_first():
    ranking = _titles(_service().rank("Anime", "Death Note"))
    assert ranking[0] in ("Monster", "Code Geass")
    assert ranking.index("Monster") < ranking.index("Kimetsu no Yaiba")


def test_the_secret_itself_is_not_in_the_ranking():
    assert "Death Note" not in _titles(_service().rank("Anime", "Death Note"))


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
    # Code Geass, pas Psycho-Pass : depuis que le percentile compte les œuvres
    # STRICTEMENT dépassées (au lieu d'une position d'index), Psycho-Pass -- 2e du
    # classement sur 6, directement recommandée depuis Death Note ET partageant
    # Detective + Philosophy -- lit 80 % et devient brûlante, ce qu'elle est. Sur un
    # fixture de 6 œuvres, le percentile avance par pas de 20 : la bande tiède
    # [50, 80) n'a de place que pour une seule œuvre, Code Geass (60 %).
    warm = _service().report("Anime", "Death Note", "Code Geass")
    assert 50 <= warm["percent"] < 80
    assert len(warm["reasons"]) == 1
    assert warm["reasons"][0]["detail"] == []  # le contenu n'apparaît qu'à HOT


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
    ranking = _titles(_service(works=games).rank("Game", "Game A"))
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
    ranking = _titles(_service(works=characters).rank("Character", "Levi"))
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


def test_a_ranking_of_bare_titles_is_still_understood():
    # Un classement mis en cache par une version antérieure (une liste de titres,
    # sans les scores) ne doit ni planter, ni mentir : le service recalcule ce
    # qu'il lui manque plutôt que de deviner.
    service = _service()
    titles = [title for title, _ in service.rank("Anime", "Death Note")]
    legacy = service.report("Anime", "Death Note", "Monster", ranking=titles)
    assert legacy == service.report("Anime", "Death Note", "Monster")


# --------------------------------------------------------------------------- #
# CRITIQUE 1 -- le percentile se calcule sur les SCORES, pas sur une position
# --------------------------------------------------------------------------- #
def test_a_zero_score_work_reports_zero_percent_not_its_place_in_the_alphabet():
    # Sur le vrai catalogue personnages, 32 280 des 32 384 noms scorent EXACTEMENT
    # 0 face à Levi. Classés par (-score, titre), ils occupaient les rangs 105 à
    # 32 384 -- par ordre alphabétique. Un personnage sans le moindre lien lisait
    # « 99,7 %, Brûlant » parce que son nom tombe tôt dans l'alphabet. Le
    # percentile d'une proposition froide ne doit pas être une fonction de son nom.
    service = _service(_one_signal_catalogue())
    cold = [
        service.report("Anime", "Secret", f"Filler {i}")["percent"] for i in range(10)
    ]
    assert cold == [0.0] * 10  # « elles sortent toutes glacial, ce qui est la vérité »


def test_works_that_tie_share_a_rank():
    service = _service(_one_signal_catalogue())
    ranks = {
        service.report("Anime", "Secret", f"Filler {i}")["rank"] for i in range(10)
    }
    assert len(ranks) == 1  # même score, même rang -- pas dix rangs consécutifs


def test_one_hundred_percent_means_nothing_is_closer():
    # L'invariant de la spec. Il n'est vrai que si le percentile compte les œuvres
    # STRICTEMENT en dessous : le premier du classement les dépasse toutes.
    service = _service(_one_signal_catalogue())
    assert service.report("Anime", "Secret", "Neighbour")["percent"] == 100.0
    assert service.report("Anime", "Secret", "Neighbour")["rank"] == 1


def test_a_work_that_is_not_the_closest_never_reports_one_hundred_percent():
    # Sur 32 384 personnages, le 15e meilleur score dépasse 99,96 % du catalogue :
    # arrondi à une décimale, il lirait « 100 % » alors que quatorze personnages
    # sont plus proches. 100 % est réservé à « rien n'est plus proche ».
    catalogue = [
        _work("Secret", recommendations={"Best": 3000, "Second": 2999}),
        _work("Best", recommendations={"Secret": 3000}),
        _work("Second", recommendations={"Secret": 2999}),
    ] + [_work(f"Filler {i}") for i in range(2000)]
    service = _service(catalogue)
    assert service.report("Anime", "Secret", "Best")["percent"] == 100.0
    assert service.report("Anime", "Secret", "Second")["percent"] < 100.0


# --------------------------------------------------------------------------- #
# IMPORTANT 2 -- le bridage tient aussi sur le SCORE BRUT, pas seulement le rang
# --------------------------------------------------------------------------- #
def test_a_high_percentile_with_a_noise_level_raw_score_reveals_nothing():
    # Une recommandation à UN vote : le percentile la place haut (elle dépasse
    # toute la traîne à zéro), mais le signal brut est du bruit. Mesuré sur le vrai
    # catalogue : le 80e percentile de DEATH NOTE est à 0,058 de score brut, et
    # 436 œuvres (20 % du catalogue) franchissaient le seuil HOT -- une romcom qui
    # ne partage que « Primarily Male Cast » se voyait offrir trois tags du secret.
    works = _one_signal_catalogue(
        extra=[_work("Whisper", recommendations={"Secret": 1})]
    )
    service = _service(works)
    index = build_index(works)
    raw = score(index, "Secret", "Whisper").total()
    assert raw < WARM_FLOOR  # du bruit

    report = service.report("Anime", "Secret", "Whisper")
    assert report["percent"] >= 80.0  # le rang, lui, la dit brûlante
    assert report["reasons"] == []  # et pourtant : rien ne se révèle


def test_a_raw_score_between_the_two_floors_names_a_component_but_not_its_content():
    works = _one_signal_catalogue(
        extra=[
            _work(
                "Warm",
                tags=["Detective"],
                recommendations={"Secret": 20},
            )
        ]
    )
    service = _service(works)
    index = build_index(works)
    raw = score(index, "Secret", "Warm").total()
    assert WARM_FLOOR <= raw < HOT_FLOOR

    report = service.report("Anime", "Secret", "Warm")
    assert report["percent"] >= 80.0  # chaud au rang...
    assert len(report["reasons"]) == 1  # ... mais bridé par le score brut
    assert report["reasons"][0]["detail"] == []


def test_only_a_raw_score_above_the_hot_floor_hands_over_the_contents():
    service = _service(_one_signal_catalogue())
    index = build_index(_one_signal_catalogue())
    assert score(index, "Secret", "Neighbour").total() >= HOT_FLOOR

    report = service.report("Anime", "Secret", "Neighbour")
    assert report["percent"] >= 80.0
    assert len(report["reasons"]) >= 1


# --------------------------------------------------------------------------- #
# IMPORTANT 3 -- un titre hors catalogue est la proposition la plus FROIDE
# --------------------------------------------------------------------------- #
def test_an_unknown_title_is_the_coldest_answer_not_the_hottest():
    # report() est l'unique couture de scoring de DEUX jeux (classique et duel).
    # Le duel ne validait pas la proposition : une trame websocket portant un titre
    # inventé diffusait « 100 % » à toute la salle. Rendre le score MAXIMAL pour
    # « je ne connais pas ce titre » est le défaut le plus dangereux possible.
    report = _service().report("Anime", "Death Note", "Un titre qui n'existe pas")
    assert report["percent"] == 0.0
    assert report["reasons"] == []
    assert report["rank"] == report["total"]


def test_the_secret_itself_is_still_the_closest_thing_there_is():
    # Le mode Classique appelle report() même sur une proposition GAGNANTE (il
    # remplace ensuite le score par 100). Le secret n'est pas dans le classement :
    # il ne doit pas être confondu avec un titre inconnu et retomber à 0.
    report = _service().report("Anime", "Death Note", "Death Note")
    assert report["percent"] == 100.0
    assert report["reasons"] == []
