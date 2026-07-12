# tests/core/test_world_boss_archetypes_relational.py
"""Bands C and D — the relational half of the game.

These are the questions you cannot answer by having watched one show. The tests
pin the two properties that make them fair: the answer is always a real catalogue
value, and a plot summary never contains its own answer.
"""

import random

import pytest
from core.domain.services.world_boss import (
    archetypes_relational,  # noqa: F401  (registers the archetypes)
)
from core.domain.services.world_boss.context import QuizContext
from core.domain.services.world_boss.registry import ARCHETYPES, archetypes_for

from tests.core.test_world_boss_archetypes_core import ANIMES, CHARACTERS

THEMES = {
    "1": {
        "title": "Kimetsu no Yaiba",
        "themes": [
            {
                "type": "OP",
                "song_title": "Gurenge",
                "artists": ["LiSA"],
                "entries": [{"version": 1, "episodes": "1-15"}],
            }
        ],
    },
    "2": {
        "title": "Jujutsu Kaisen",
        "themes": [
            {
                "type": "OP",
                "song_title": "Kaikai Kitan",
                "artists": ["Eve"],
                "entries": [{"version": 1, "episodes": "1-13"}],
            }
        ],
    },
    "4": {
        "title": "Cowboy Bebop",
        "themes": [
            {
                "type": "OP",
                "song_title": "Tank!",
                "artists": ["The Seatbelts"],
                "entries": [{"version": 1, "episodes": "1-26"}],
            }
        ],
    },
    "7": {
        "title": "Steins;Gate",
        "themes": [
            {
                "type": "OP",
                "song_title": "Hacking to the Gate",
                "artists": ["Kanako Ito"],
                "entries": [{"version": 1, "episodes": "1-24"}],
            }
        ],
    },
    "6": {
        "title": "Chainsaw Man",
        "themes": [
            {
                "type": "OP",
                "song_title": "Kick Back",
                "artists": ["Kenshi Yonezu"],
                "entries": [{"version": 1, "episodes": "1-12"}],
            }
        ],
    },
}

EPISODES = {
    "11": [
        {
            "number": 1,
            "title": "Cruelty",
            "synopsis": "Kimetsu no Yaiba opens as Tanjiro comes home to a slaughtered family.",
        }
    ],
    "12": [
        {
            "number": 1,
            "title": "Ryomen Sukuna",
            "synopsis": "Yuji swallows a cursed finger.",
        }
    ],
    "14": [
        {
            "number": 1,
            "title": "Asteroid Blues",
            "synopsis": "Spike and Jet chase a bounty on Tijuana.",
        }
    ],
    "17": [
        {
            "number": 1,
            "title": "Turning Point",
            "synopsis": "Okabe witnesses a murder that unhappens.",
        }
    ],
    "18": [
        {
            "number": 1,
            "title": "Somewhere Not Here",
            "synopsis": "Thorfinn sails with the man who killed his father.",
        }
    ],
}

RELATIONAL = [
    "opening_to_work",
    "shared_tag",
    "not_recommended",
    "same_work_character",
    "secondary_character",
    "episode_title",
    "sequel",
    "not_studio",
    "opening_artist",
    "exact_year",
    "top_recommendation",
    "rare_tag",
    "episode_synopsis",
    "character_sheet",
    "opening_range",
]

SHEETED = {
    "Kimetsu no Yaiba": CHARACTERS["Kimetsu no Yaiba"],
    "Cowboy Bebop": CHARACTERS["Cowboy Bebop"],
    "Monster": CHARACTERS["Monster"],
}
for name, org in (
    ("Kimetsu no Yaiba", "Demon Slayer Corps"),
    ("Cowboy Bebop", "Bebop Crew"),
    ("Monster", "BKA"),
):
    for char in SHEETED[name]:
        char["entities"] = {"organizations": [org]}

# A tag that exists on exactly one work, so `rare_tag` has something to find.
ANIMES_WITH_SEQUEL = [dict(a) for a in ANIMES]
ANIMES_WITH_SEQUEL[1]["relations"] = {"SEQUEL": ["Shibuya Incident"]}
ANIMES_WITH_SEQUEL[3]["relations"] = {"SEQUEL": ["Knockin' on Heaven's Door"]}
ANIMES_WITH_SEQUEL[5]["relations"] = {"SEQUEL": ["Chainsaw Man: Reze"]}

# `not_recommended` needs a subject with >= 3 recommendations, `top_recommendation`
# needs >= 4: the base fixture only gives Kimetsu 2, so both would decline outright.
ANIMES_WITH_SEQUEL[0]["recommendations"] = {
    "Jujutsu Kaisen": 300,
    "Chainsaw Man": 80,
    "Vinland Saga": 60,
    "Monster": 40,
}

# `not_studio` needs a studio shared by >= 3 works to have distractors to sample;
# the base fixture tops out at MAPPA x2 (Jujutsu Kaisen, Chainsaw Man). Add Fruits
# Basket as a second studio without erasing its original TMS credit.
ANIMES_WITH_SEQUEL[2]["studios"] = ["TMS", "MAPPA"]


def ctx(closeness=1.0):
    return QuizContext(
        animes=ANIMES_WITH_SEQUEL,
        pool=ANIMES_WITH_SEQUEL,
        themes=THEMES,
        episodes=EPISODES,
        characters_by_origin=SHEETED,
        closeness=closeness,
    )


@pytest.mark.parametrize("name", RELATIONAL)
def test_every_relational_archetype_builds_a_four_option_question(name):
    questions = [
        q
        for q in (ARCHETYPES[name].build(ctx(), random.Random(s)) for s in range(40))
        if q
    ]

    assert (
        questions
    ), f"{name} never produced a question on a catalogue that has its data"
    for q in questions:
        assert len(set(q.options)) == 4
        assert q.archetype == name


@pytest.mark.parametrize("name", RELATIONAL)
def test_every_relational_archetype_declines_when_the_data_is_missing(name):
    bare = QuizContext(
        animes=ANIMES,
        pool=ANIMES,
        themes={},
        episodes={},
        characters_by_origin={},
        closeness=1.0,
    )

    built = ARCHETYPES[name].build(bare, random.Random(1))

    # No themes, no episodes, no cast: an archetype either declines outright or
    # answers from the catalogue alone. What it must never do is invent.
    assert built is None or (len(set(built.options)) == 4 and built.archetype == name)


def test_the_bands_hold_the_expected_archetypes():
    assert {a.name for a in archetypes_for("C")} == {
        "opening_to_work",
        "shared_tag",
        "not_recommended",
        "same_work_character",
        "secondary_character",
        "episode_title",
        "sequel",
        "not_studio",
    }
    assert {a.name for a in archetypes_for("D")} == {
        "opening_artist",
        "exact_year",
        "top_recommendation",
        "rare_tag",
        "episode_synopsis",
        "character_sheet",
        "opening_range",
    }


def test_a_plot_summary_never_names_its_own_work():
    for seed in range(40):
        q = ARCHETYPES["episode_synopsis"].build(ctx(), random.Random(seed))
        if q and q.subject == "Kimetsu no Yaiba":
            assert "Kimetsu" not in q.prompt and "Yaiba" not in q.prompt
            assert "Tanjiro" in q.prompt  # the story survives, only the title is hidden
            return
    pytest.fail("episode_synopsis never drew the masked work")


def test_the_top_recommendation_is_the_highest_rated_one():
    # Kimetsu recommends Jujutsu Kaisen (300) over Chainsaw Man (80).
    for seed in range(40):
        q = ARCHETYPES["top_recommendation"].build(ctx(), random.Random(seed))
        if q:
            assert q.options[q.correct_index] == "Jujutsu Kaisen"
            return
    pytest.fail("top_recommendation never produced a question")


def test_shared_tag_answers_with_a_tag_both_works_carry():
    for seed in range(40):
        q = ARCHETYPES["shared_tag"].build(ctx(), random.Random(seed))
        if not q:
            continue
        titles = [t.strip() for t in q.prompt.split("«")[1:3]]
        # split("»")[0] leaves the interior space French typography puts before the
        # closing guillemet (e.g. "Jujutsu Kaisen "); strip it before matching titles.
        first, second = (t.split("»")[0].strip() for t in titles)
        a = next(x for x in ANIMES_WITH_SEQUEL if x["title"] == first)
        b = next(x for x in ANIMES_WITH_SEQUEL if x["title"] == second)
        answer = q.options[q.correct_index]
        assert answer in a["tags"] and answer in b["tags"]
        for i, option in enumerate(q.options):
            if i != q.correct_index:
                assert not (option in a["tags"] and option in b["tags"])
        return
    pytest.fail("shared_tag never produced a question")


def test_not_recommended_answers_with_the_one_that_is_not():
    for seed in range(40):
        q = ARCHETYPES["not_recommended"].build(ctx(), random.Random(seed))
        if not q:
            continue
        subject = next(a for a in ANIMES_WITH_SEQUEL if a["title"] == q.subject)
        assert q.options[q.correct_index] not in subject["recommendations"]
        for i, option in enumerate(q.options):
            if i != q.correct_index:
                assert option in subject["recommendations"]
        return
    pytest.fail("not_recommended never produced a question")
