# tests/core/test_world_boss_archetypes_core.py
"""Bands A and B. Every archetype must produce a question whose answer is a real
catalogue value, and must decline (None) rather than invent when the data is missing."""

import random

import pytest
from core.domain.services.world_boss import (
    archetypes_core,  # noqa: F401  (registers the archetypes)
)
from core.domain.services.world_boss.context import QuizContext
from core.domain.services.world_boss.registry import ARCHETYPES, archetypes_for

ANIMES = [
    {
        "id": 1,
        "idMal": 11,
        "title": "Kimetsu no Yaiba",
        "year": 2019,
        "popularity": 900000,
        "genres": ["Action", "Adventure"],
        "tags": ["Demons", "Swordplay"],
        "studios": ["ufotable"],
        "source": "MANGA",
        "image": "kny.jpg",
        "recommendations": {"Jujutsu Kaisen": 300, "Chainsaw Man": 80},
        "relations": {"SEQUEL": ["Mugen Train"]},
    },
    {
        "id": 2,
        "idMal": 12,
        "title": "Jujutsu Kaisen",
        "year": 2020,
        "popularity": 800000,
        "genres": ["Action", "Supernatural"],
        "tags": ["Curses", "Demons"],
        "studios": ["MAPPA"],
        "source": "MANGA",
        "image": "jjk.jpg",
        "recommendations": {"Kimetsu no Yaiba": 250},
        "relations": {},
    },
    {
        "id": 3,
        "idMal": 13,
        "title": "Fruits Basket",
        "year": 2001,
        "popularity": 300000,
        "genres": ["Romance", "Drama"],
        "tags": ["Curses", "Family"],
        "studios": ["TMS"],
        "source": "MANGA",
        "image": "fb.jpg",
        "recommendations": {},
        "relations": {},
    },
    {
        "id": 4,
        "idMal": 14,
        "title": "Cowboy Bebop",
        "year": 1998,
        "popularity": 500000,
        "genres": ["Sci-Fi", "Action"],
        "tags": ["Space", "Bounty Hunters"],
        "studios": ["Sunrise"],
        "source": "ORIGINAL",
        "image": "bebop.jpg",
        "recommendations": {},
        "relations": {},
    },
    {
        "id": 5,
        "idMal": 15,
        "title": "Monster",
        "year": 2004,
        "popularity": 200000,
        "genres": ["Thriller", "Drama"],
        "tags": ["Serial Killers"],
        "studios": ["Madhouse"],
        "source": "MANGA",
        "image": "monster.jpg",
        "recommendations": {},
        "relations": {},
    },
    {
        "id": 6,
        "idMal": 16,
        "title": "Chainsaw Man",
        "year": 2022,
        "popularity": 400000,
        "genres": ["Action", "Horror"],
        "tags": ["Demons", "Gore"],
        "studios": ["MAPPA"],
        "source": "MANGA",
        "image": "csm.jpg",
        "recommendations": {},
        "relations": {},
    },
    {
        "id": 7,
        "idMal": 17,
        "title": "Steins;Gate",
        "year": 2011,
        "popularity": 600000,
        "genres": ["Sci-Fi", "Thriller"],
        "tags": ["Time Travel"],
        "studios": ["White Fox"],
        "source": "VISUAL_NOVEL",
        "image": "sg.jpg",
        "recommendations": {},
        "relations": {},
    },
    {
        "id": 8,
        "idMal": 18,
        "title": "Vinland Saga",
        "year": 2019,
        "popularity": 350000,
        "genres": ["Action", "Historical"],
        "tags": ["Vikings"],
        "studios": ["Wit Studio"],
        "source": "MANGA",
        "image": "vs.jpg",
        "recommendations": {},
        "relations": {},
    },
]

CHARACTERS = {
    "Kimetsu no Yaiba": [
        {
            "name": "Tanjiro Kamado",
            "origin": "Kimetsu no Yaiba",
            "popularity": {"favourites": 30000, "rank": 3},
        },
        {
            "name": "Zenitsu",
            "origin": "Kimetsu no Yaiba",
            "popularity": {"favourites": 200, "rank": 900},
        },
    ],
    "Cowboy Bebop": [
        {
            "name": "Spike Spiegel",
            "origin": "Cowboy Bebop",
            "popularity": {"favourites": 25000, "rank": 8},
        },
        {
            "name": "Ed",
            "origin": "Cowboy Bebop",
            "popularity": {"favourites": 150, "rank": 950},
        },
    ],
    "Monster": [
        {
            "name": "Johan Liebert",
            "origin": "Monster",
            "popularity": {"favourites": 20000, "rank": 12},
        },
    ],
}


def ctx(closeness=0.0, pool=None):
    return QuizContext(
        animes=ANIMES,
        pool=pool or ANIMES,
        themes={},
        episodes={},
        characters_by_origin=CHARACTERS,
        closeness=closeness,
    )


CORE = [
    "year",
    "genre",
    "cover",
    "most_popular",
    "oldest",
    "tag",
    "character_origin",
    "recommended",
    "released_first",
    "source",
    "studio",
    "not_genre",
]


@pytest.mark.parametrize("name", CORE)
def test_every_core_archetype_builds_a_four_option_question(name):
    built = [ARCHETYPES[name].build(ctx(), random.Random(seed)) for seed in range(30)]
    questions = [q for q in built if q is not None]

    assert (
        questions
    ), f"{name} never produced a question on a catalogue that has its data"
    for q in questions:
        assert len(q.options) == 4
        assert len(set(q.options)) == 4
        assert q.options[q.correct_index]
        assert q.archetype == name


@pytest.mark.parametrize("name", CORE)
def test_every_core_archetype_declines_on_an_empty_catalogue(name):
    empty = QuizContext(
        animes=[],
        pool=[],
        themes={},
        episodes={},
        characters_by_origin={},
        closeness=0.0,
    )
    assert ARCHETYPES[name].build(empty, random.Random(1)) is None


def test_the_bands_hold_the_expected_archetypes():
    assert {a.name for a in archetypes_for("A")} == {
        "year",
        "genre",
        "cover",
        "most_popular",
        "oldest",
    }
    assert {a.name for a in archetypes_for("B")} == {
        "tag",
        "character_origin",
        "recommended",
        "released_first",
        "source",
        "studio",
        "not_genre",
    }


def test_the_year_answer_is_the_real_year():
    q = next(ARCHETYPES["year"].build(ctx(), random.Random(s)) for s in range(5))
    subject = next(a for a in ANIMES if a["title"] == q.subject)
    assert q.options[q.correct_index] == str(subject["year"])


def test_year_distractors_close_in_with_the_tier():
    def spread(closeness):
        widths = []
        for seed in range(40):
            q = ARCHETYPES["year"].build(ctx(closeness=closeness), random.Random(seed))
            if q:
                years = [int(o) for o in q.options]
                widths.append(max(years) - min(years))
        return sum(widths) / len(widths)

    assert spread(1.0) < spread(0.0)


def test_the_cover_question_ships_the_image_of_its_subject():
    q = next(
        q
        for q in (ARCHETYPES["cover"].build(ctx(), random.Random(s)) for s in range(5))
        if q
    )
    subject = next(a for a in ANIMES if a["title"] == q.subject)
    assert q.image == subject["image"]


def test_the_genre_distractors_are_genres_the_work_does_not_have():
    for seed in range(20):
        q = ARCHETYPES["genre"].build(ctx(), random.Random(seed))
        if not q:
            continue
        subject = next(a for a in ANIMES if a["title"] == q.subject)
        for i, option in enumerate(q.options):
            assert (option in subject["genres"]) == (i == q.correct_index)


def test_the_recommended_answer_really_is_recommended():
    for seed in range(30):
        q = ARCHETYPES["recommended"].build(ctx(), random.Random(seed))
        if not q:
            continue
        subject = next(a for a in ANIMES if a["title"] == q.subject)
        assert q.options[q.correct_index] in subject["recommendations"]
        for i, option in enumerate(q.options):
            if i != q.correct_index:
                assert option not in subject["recommendations"]


def test_not_genre_answers_with_the_odd_one_out():
    for seed in range(30):
        q = ARCHETYPES["not_genre"].build(ctx(), random.Random(seed))
        if not q:
            continue
        genre = q.prompt.split("«")[1].split("»")[0].strip()
        answer = next(a for a in ANIMES if a["title"] == q.options[q.correct_index])
        assert genre not in answer["genres"]
        for i, option in enumerate(q.options):
            if i != q.correct_index:
                assert (
                    genre in next(a for a in ANIMES if a["title"] == option)["genres"]
                )
