"""The four components of the proximity signal.

The embedding this replaces put Kimetsu no Yaiba closer to Death Note (0.671)
than Monster is (0.654), on a catalogue whose random-pair baseline is 0.583.
These tests pin the properties that make the new signal honest: rarity beats
frequency, the recommendation graph carries the human judgement, and a bonus
can never carry a score on its own.
"""

import pytest
from core.domain.services.proximity.components import (
    BONUS_CAP,
    W_CO_RECO,
    W_DIRECT,
    W_TAGS,
    build_index,
    co_reco,
    direct_reco,
    score,
    structural_bonus,
    tag_overlap,
)

# Un catalogue jouet, mais dont les liens sont ceux du vrai : Death Note et Monster
# sont recommandés l'un à l'autre ; Kimetsu n'a aucun lien avec eux.
WORKS = [
    {
        "title": "Death Note",
        "tags": ["Detective", "Philosophy", "Primarily Male Cast"],
        "genres": ["Mystery", "Thriller"],
        "studios": ["MADHOUSE"],
        "source": "MANGA",
        "year": 2006,
        "relations": {},
        "recommendations": {"Monster": 1151, "Code Geass": 3473, "Psycho-Pass": 200},
    },
    {
        "title": "Monster",
        "tags": ["Detective", "Philosophy", "Primarily Male Cast"],
        "genres": ["Mystery", "Thriller"],
        "studios": ["MADHOUSE"],
        "source": "MANGA",
        "year": 2004,
        "relations": {},
        "recommendations": {"Death Note": 900, "Psycho-Pass": 150},
    },
    {
        "title": "Code Geass",
        "tags": ["Philosophy", "Primarily Male Cast"],
        "genres": ["Mecha"],
        "studios": ["Sunrise"],
        "source": "ORIGINAL",
        "year": 2006,
        "relations": {},
        # Pas de "Psycho-Pass" ici : le fixture original du brief en avait un (90 votes),
        # ce qui créait une arête directe et contredisait le commentaire du test
        # test_co_reco_finds_a_link_with_no_direct_edge ("ne se recommandent pas l'un
        # l'autre"). direct_reco(index, a, b) était alors > 0 alors que le test
        # attendait 0.0 -- bug de fixture, pas de code : direct_reco prend bien "l'arête
        # la plus votée des deux sens" comme documenté, il n'y avait simplement pas
        # censé y avoir d'arête ici.
        "recommendations": {"Death Note": 3000},
    },
    {
        "title": "Psycho-Pass",
        "tags": ["Detective", "Philosophy"],
        "genres": ["Thriller"],
        "studios": ["Production I.G"],
        "source": "ORIGINAL",
        "year": 2012,
        "relations": {},
        "recommendations": {"Death Note": 400, "Monster": 120},
    },
    {
        "title": "Kimetsu no Yaiba",
        "tags": ["Demons", "Swordplay", "Primarily Male Cast"],
        "genres": ["Action"],
        "studios": ["ufotable"],
        "source": "MANGA",
        "year": 2019,
        "relations": {"SEQUEL": ["Mugen Train"]},
        "recommendations": {"Jujutsu Kaisen": 300},
    },
    {
        "title": "Jujutsu Kaisen",
        "tags": ["Demons", "Curses", "Primarily Male Cast"],
        "genres": ["Action"],
        "studios": ["MAPPA"],
        "source": "MANGA",
        "year": 2020,
        "relations": {},
        "recommendations": {"Kimetsu no Yaiba": 250},
    },
    {
        "title": "Mugen Train",
        "tags": ["Demons", "Swordplay"],
        "genres": ["Action"],
        "studios": ["ufotable"],
        "source": "MANGA",
        "year": 2021,
        "relations": {"PREQUEL": ["Kimetsu no Yaiba"]},
        "recommendations": {},
    },
]

INDEX = build_index(WORKS)


def test_the_bug_this_replaces_monster_beats_kimetsu_for_death_note():
    # L'embedding disait l'inverse. C'est LE test de non-régression du design.
    assert (
        score(INDEX, "Death Note", "Monster").total()
        > score(INDEX, "Death Note", "Kimetsu no Yaiba").total()
    )


def test_a_work_with_no_link_at_all_scores_zero():
    assert score(INDEX, "Death Note", "Kimetsu no Yaiba").direct == 0.0
    assert score(INDEX, "Death Note", "Kimetsu no Yaiba").co_reco == 0.0


def test_direct_reco_is_symmetric_and_takes_the_stronger_edge():
    # Death Note -> Monster (1151) et Monster -> Death Note (900) : on garde 1151.
    assert direct_reco(INDEX, "Death Note", "Monster") == direct_reco(
        INDEX, "Monster", "Death Note"
    )
    assert direct_reco(INDEX, "Death Note", "Monster") > direct_reco(
        INDEX, "Monster", "Psycho-Pass"
    )


def test_co_reco_finds_a_link_with_no_direct_edge():
    # Code Geass et Psycho-Pass ne se recommandent pas l'un l'autre, mais tous deux
    # recommandent Death Note : le public les rapproche. C'est toute la densité du signal.
    assert direct_reco(INDEX, "Code Geass", "Psycho-Pass") == 0.0
    assert co_reco(INDEX, "Code Geass", "Psycho-Pass") > 0.0


def test_a_rare_tag_is_worth_more_than_a_banal_one():
    # "Primarily Male Cast" est porté par presque tout le catalogue ; "Detective" par peu.
    # Deux oeuvres qui ne partagent QUE le tag banal doivent scorer sous deux qui
    # partagent le tag rare.
    banal_only = tag_overlap(
        INDEX, "Code Geass", "Kimetsu no Yaiba"
    )  # Primarily Male Cast
    rare_shared = tag_overlap(
        INDEX, "Death Note", "Psycho-Pass"
    )  # Detective + Philosophy
    assert rare_shared > banal_only


def test_the_structural_bonus_never_carries_a_score_alone():
    # Deux oeuvres du même studio, même source, même décennie -- mais aucun lien de
    # recommandation ni tag partagé -> le bonus est neutralisé.
    lonely = [
        {
            "title": "A",
            "tags": [],
            "genres": [],
            "studios": ["X"],
            "source": "MANGA",
            "year": 2001,
            "relations": {},
            "recommendations": {},
        },
        {
            "title": "B",
            "tags": [],
            "genres": [],
            "studios": ["X"],
            "source": "MANGA",
            "year": 2002,
            "relations": {},
            "recommendations": {},
        },
    ]
    idx = build_index(lonely)
    assert structural_bonus(idx, "A", "B") > 0  # le bonus brut existe...
    assert score(idx, "A", "B").total() == 0.0  # ... mais il est porté à zéro


def test_a_franchise_link_is_the_strongest_bonus():
    assert structural_bonus(INDEX, "Kimetsu no Yaiba", "Mugen Train") == pytest.approx(
        BONUS_CAP
    )


def test_the_score_is_bounded():
    assert 0.0 <= score(INDEX, "Death Note", "Monster").total() <= 1.0
    assert score(INDEX, "Death Note", "Death Note").total() <= 1.0


def test_the_weights_are_the_ones_the_spec_measured():
    assert (W_DIRECT, W_CO_RECO, W_TAGS, BONUS_CAP) == (0.45, 0.30, 0.25, 0.15)
