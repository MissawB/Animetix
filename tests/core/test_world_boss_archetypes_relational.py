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
    name: [dict(c) for c in CHARACTERS[name]]
    for name in ("Kimetsu no Yaiba", "Cowboy Bebop", "Monster")
}
for name, org in (
    ("Kimetsu no Yaiba", "Demon Slayer Corps"),
    ("Cowboy Bebop", "Bebop Crew"),
    ("Monster", "BKA"),
):
    for char in SHEETED[name]:
        char["entities"] = {"organizations": [org]}

# `secondary_character` needs a work with >= 3 known characters (the base
# fixture tops out at 2 per work): give Kimetsu no Yaiba a third castmate, less
# loved than both Tanjiro and Zenitsu, so it has a genuine "rest of the cast".
SHEETED["Kimetsu no Yaiba"].append(
    {
        "name": "Inosuke",
        "origin": "Kimetsu no Yaiba",
        "popularity": {"favourites": 90, "rank": 950},
        "entities": {"organizations": ["Demon Slayer Corps"]},
    }
)

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


def test_secondary_character_treats_a_float_popularity_as_unranked_not_a_crash():
    # `_rank` read `(character.get("popularity") or {}).get("rank")` -- the
    # identical latent bug `_favourites` (archetypes_core.py) was fixed for.
    # Servi par la base, un personnage porte `popularity` comme un FLOAT (la
    # colonne brute), jamais le dict {"favourites", "rank"} que le JSON fournit
    # -- `.get("rank")` sur ce float lève un AttributeError.
    characters = {
        "Work A": [
            {"name": "Star", "popularity": {"favourites": 1000, "rank": 1}},
            {"name": "Obscure", "popularity": 42.0},
        ],
    }
    pool = [{"title": "Work A"}]
    float_ctx = QuizContext(
        animes=pool,
        pool=pool,
        themes={},
        episodes={},
        characters_by_origin=characters,
        closeness=1.0,
    )
    for seed in range(20):
        ARCHETYPES["secondary_character"].build(float_ctx, random.Random(seed))


def test_secondary_character_fires_on_the_real_datas_small_per_work_ranks():
    # The bug this whole rewrite exists for: in `data/processed/filtered_
    # characters.json`, `rank` is a SMALL PER-WORK integer, not a global
    # popularity rank -- Dororo's own cast comes back ranked 1 and 2. The old
    # `_rank(c) > 200` threshold was therefore never true and the archetype
    # fired 0/50 on the real catalogue. "Secondary" must come from the work's
    # OWN cast ordering (by `favourites`), which this fixture reproduces:
    # every rank is small (1, 2, 3), exactly the real shape.
    characters = {
        "Dororo": [
            {
                "name": "Hyakkimaru",
                "origin": "Dororo",
                "popularity": {"favourites": 5000, "rank": 1},
            },
            {
                "name": "Mio",
                "origin": "Dororo",
                "popularity": {"favourites": 3000, "rank": 2},
            },
            {
                "name": "Tahomaru",
                "origin": "Dororo",
                "popularity": {"favourites": 800, "rank": 3},
            },
        ],
        "Other Show": [
            {
                "name": "Gamma",
                "origin": "Other Show",
                "popularity": {"favourites": 500, "rank": 1},
            },
            {
                "name": "Delta",
                "origin": "Other Show",
                "popularity": {"favourites": 400, "rank": 2},
            },
        ],
        "Third Show": [
            {
                "name": "Epsilon",
                "origin": "Third Show",
                "popularity": {"favourites": 300, "rank": 1},
            },
            {
                "name": "Zeta",
                "origin": "Third Show",
                "popularity": {"favourites": 200, "rank": 2},
            },
        ],
    }
    pool = [{"title": "Dororo"}, {"title": "Other Show"}, {"title": "Third Show"}]
    real_ctx = QuizContext(
        animes=pool,
        pool=pool,
        themes={},
        episodes={},
        characters_by_origin=characters,
        closeness=1.0,
    )
    seen_dororo = False
    for seed in range(60):
        q = ARCHETYPES["secondary_character"].build(real_ctx, random.Random(seed))
        if not q or q.subject != "Dororo":
            continue
        seen_dororo = True
        answer = q.options[q.correct_index]
        # Hyakkimaru and Mio are Dororo's two most-loved characters (by
        # `favourites`) -- the answer must be the one left outside that top 2.
        assert answer == "Tahomaru"
        assert answer not in {"Hyakkimaru", "Mio"}
    assert seen_dororo, "secondary_character never fired on the real-data rank shape"


def test_secondary_character_declines_when_a_work_has_fewer_than_three_known_characters():
    # Below 3 known characters there is no "rest of the cast" beyond the top 2
    # to ask about -- the archetype must decline (None), not compose a broken
    # question, and it must never raise while trying.
    characters = {
        "Two Cast Show": [
            {
                "name": "Alpha",
                "origin": "Two Cast Show",
                "popularity": {"favourites": 100, "rank": 1},
            },
            {
                "name": "Beta",
                "origin": "Two Cast Show",
                "popularity": {"favourites": 50, "rank": 2},
            },
        ],
    }
    pool = [{"title": "Two Cast Show"}]
    thin_ctx = QuizContext(
        animes=pool,
        pool=pool,
        themes={},
        episodes={},
        characters_by_origin=characters,
        closeness=1.0,
    )
    for seed in range(60):
        assert (
            ARCHETYPES["secondary_character"].build(thin_ctx, random.Random(seed))
            is None
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


def test_character_sheet_never_offers_a_dual_org_character_as_a_wrong_answer():
    # D belongs to BOTH Org X and Org Z. `enrolled` flattens one row per
    # (work, character, organisation), so D surfaces twice -- once per
    # organisation it holds. A question about Org X must never offer D as a
    # WRONG option: D genuinely belongs to Org X too, via its own other row.
    dual_sheet = {
        "Work W": [
            {"name": "D", "entities": {"organizations": ["Org X", "Org Z"]}},
            {"name": "F", "entities": {"organizations": ["Org X"]}},
        ],
        "Work Y": [
            {"name": "G", "entities": {"organizations": ["Org Y"]}},
            {"name": "H", "entities": {"organizations": ["Org Y"]}},
        ],
        "Work V": [
            {"name": "I", "entities": {"organizations": ["Org Z"]}},
        ],
    }
    pool = [{"title": "Work W"}, {"title": "Work Y"}, {"title": "Work V"}]
    dual_ctx = QuizContext(
        animes=pool,
        pool=pool,
        themes={},
        episodes={},
        characters_by_origin=dual_sheet,
        closeness=1.0,
    )
    seen_org_x_question = False
    for seed in range(60):
        q = ARCHETYPES["character_sheet"].build(dual_ctx, random.Random(seed))
        if not q or "Org X" not in q.prompt:
            continue
        seen_org_x_question = True
        wrong = {o for i, o in enumerate(q.options) if i != q.correct_index}
        assert "D" not in wrong, "D belongs to Org X too -- it cannot be a wrong answer"
    assert seen_org_x_question, "character_sheet never asked about Org X"


def test_same_work_character_never_pulls_a_distractor_from_a_duplicate_titled_work():
    # Two pool entries share the title "Duplicate Show" (a re-ingested season,
    # a franchise reusing its title). `_cast` keys on the TITLE, so both
    # entries resolve to the identical cast. A distractor must never come from
    # that same cast, no matter which of the two duplicate pool objects was
    # picked as the subject.
    cast = [
        {"name": "Alpha", "origin": "Duplicate Show"},
        {"name": "Beta", "origin": "Duplicate Show"},
        {"name": "Charlie", "origin": "Duplicate Show"},
    ]
    characters = {
        "Duplicate Show": cast,
        "Other Show A": [
            {"name": "Gamma", "origin": "Other Show A"},
            {"name": "Delta", "origin": "Other Show A"},
        ],
        "Other Show B": [
            {"name": "Epsilon", "origin": "Other Show B"},
            {"name": "Zeta", "origin": "Other Show B"},
        ],
    }
    pool = [
        {"title": "Duplicate Show"},
        {"title": "Duplicate Show"},
        {"title": "Other Show A"},
        {"title": "Other Show B"},
    ]
    dup_ctx = QuizContext(
        animes=pool,
        pool=pool,
        themes={},
        episodes={},
        characters_by_origin=characters,
        closeness=1.0,
    )
    cast_names = {c["name"] for c in cast}
    seen_duplicate_subject = False
    for seed in range(60):
        q = ARCHETYPES["same_work_character"].build(dup_ctx, random.Random(seed))
        if not q or q.subject != "Duplicate Show":
            continue
        seen_duplicate_subject = True
        wrong = {o for i, o in enumerate(q.options) if i != q.correct_index}
        assert not (
            cast_names & wrong
        ), "a distractor came from the subject's own (duplicate-titled) cast"
    assert (
        seen_duplicate_subject
    ), "same_work_character never picked the duplicated work"


def test_secondary_character_never_pulls_a_distractor_from_a_duplicate_titled_work():
    # Same exploit as same_work_character, on secondary_character's own distractor
    # pool: two pool entries share the title "Duplicate Show", so `_cast` (keyed on
    # TITLE) resolves both to the SAME cast list. `it is not work` only excludes the
    # exact object picked as the subject -- the OTHER "Duplicate Show" pool entry
    # sails through the identity check and leaks the subject's own castmates into
    # "elsewhere" as if they were strangers. The question asks "which secondary
    # character appears in «work»?", so a castmate offered as a wrong answer is, in
    # fact, also correct.
    cast = [
        {"name": "Alpha", "origin": "Duplicate Show"},
        {"name": "Beta", "origin": "Duplicate Show"},
        {"name": "Charlie", "origin": "Duplicate Show"},
    ]
    characters = {
        "Duplicate Show": cast,
        "Other Show A": [
            {"name": "Gamma", "origin": "Other Show A"},
            {"name": "Delta", "origin": "Other Show A"},
        ],
        "Other Show B": [
            {"name": "Epsilon", "origin": "Other Show B"},
            {"name": "Zeta", "origin": "Other Show B"},
        ],
    }
    pool = [
        {"title": "Duplicate Show"},
        {"title": "Duplicate Show"},
        {"title": "Other Show A"},
        {"title": "Other Show B"},
    ]
    dup_ctx = QuizContext(
        animes=pool,
        pool=pool,
        themes={},
        episodes={},
        characters_by_origin=characters,
        closeness=1.0,
    )
    cast_names = {c["name"] for c in cast}
    seen_duplicate_subject = False
    for seed in range(60):
        q = ARCHETYPES["secondary_character"].build(dup_ctx, random.Random(seed))
        if not q or q.subject != "Duplicate Show":
            continue
        seen_duplicate_subject = True
        wrong = {o for i, o in enumerate(q.options) if i != q.correct_index}
        assert not (
            cast_names & wrong
        ), "a distractor came from the subject's own (duplicate-titled) cast"
    assert (
        seen_duplicate_subject
    ), "secondary_character never picked the duplicated work"


def test_opening_artist_never_offers_a_co_performer_of_the_correct_song_as_a_wrong_answer():
    # "Together Now" is a duet: "Artist One" and "Artist Two" both genuinely
    # perform it -- the themes data carries `artists: [...]` straight from
    # AnimeThemes.moe, which credits every performer of a song. `_all_themes`
    # walks every theme, including the correct one, and the old filter only
    # dropped `artists[0]`, so the second credited artist survived into
    # "elsewhere" and could be offered as a WRONG answer to "who performs
    # « Together Now »?" while genuinely performing it. In a community raid,
    # a correct answer damages the shared HP pool -- that is a real exploit.
    themes = {
        "10": {
            "title": "Duet Anime",
            "themes": [
                {
                    "type": "OP",
                    "song_title": "Together Now",
                    "artists": ["Artist One", "Artist Two"],
                    "entries": [{"version": 1, "episodes": "1-12"}],
                }
            ],
        },
        "11": {
            "title": "Anime B",
            "themes": [
                {
                    "type": "OP",
                    "song_title": "Solo Song B",
                    "artists": ["Artist Three"],
                    "entries": [{"version": 1, "episodes": "1-12"}],
                }
            ],
        },
        "12": {
            "title": "Anime C",
            "themes": [
                {
                    "type": "OP",
                    "song_title": "Solo Song C",
                    "artists": ["Artist Four"],
                    "entries": [{"version": 1, "episodes": "1-12"}],
                }
            ],
        },
        "13": {
            "title": "Anime D",
            "themes": [
                {
                    "type": "OP",
                    "song_title": "Solo Song D",
                    "artists": ["Artist Five"],
                    "entries": [{"version": 1, "episodes": "1-12"}],
                }
            ],
        },
    }
    pool = [
        {"id": 10, "title": "Duet Anime"},
        {"id": 11, "title": "Anime B"},
        {"id": 12, "title": "Anime C"},
        {"id": 13, "title": "Anime D"},
    ]
    duet_ctx = QuizContext(
        animes=pool,
        pool=pool,
        themes=themes,
        episodes={},
        characters_by_origin={},
        closeness=1.0,
    )
    seen_duet = False
    for seed in range(60):
        q = ARCHETYPES["opening_artist"].build(duet_ctx, random.Random(seed))
        if not q or q.subject != "Duet Anime":
            continue
        seen_duet = True
        wrong = {o for i, o in enumerate(q.options) if i != q.correct_index}
        assert "Artist Two" not in wrong, (
            "Artist Two co-performs the correct song -- it cannot be offered "
            "as a wrong answer"
        )
    assert seen_duet, "opening_artist never picked the duet theme"


def test_sequel_never_offers_one_of_the_subjects_own_sequels_as_a_wrong_answer():
    # Same exploit `same_work_character`/`secondary_character` were fixed for:
    # two pool entries share the title "Duplicate Show" (a re-ingested season,
    # a franchise reusing its title) and carry the SAME multi-entry
    # `relations.SEQUEL` list. `others` used to exclude the chosen subject
    # only by object IDENTITY, so the duplicate-titled twin sailed through and
    # contributed the subject's OWN other sequel as a "wrong" answer -- except
    # every entry in `relations.SEQUEL` is a genuine direct sequel of the
    # subject, so that "wrong" answer is also correct. Unlike the
    # title-emitting character archetypes, a sequel title does not collide
    # textually with whichever sequel was drawn as the correct answer, so
    # `make_question`'s casefold dedupe does not catch it.
    pool = [
        {"title": "Duplicate Show", "relations": {"SEQUEL": ["Seq A", "Seq B"]}},
        {"title": "Duplicate Show", "relations": {"SEQUEL": ["Seq A", "Seq B"]}},
        {"title": "Other Show A", "relations": {"SEQUEL": ["Other A1", "Other A2"]}},
        {"title": "Other Show B", "relations": {"SEQUEL": ["Other B1"]}},
    ]
    dup_ctx = QuizContext(
        animes=pool,
        pool=pool,
        themes={},
        episodes={},
        characters_by_origin={},
        closeness=1.0,
    )
    own_sequels = {"Seq A", "Seq B"}
    seen_duplicate_subject = False
    for seed in range(60):
        q = ARCHETYPES["sequel"].build(dup_ctx, random.Random(seed))
        if not q or q.subject != "Duplicate Show":
            continue
        seen_duplicate_subject = True
        wrong = {o for i, o in enumerate(q.options) if i != q.correct_index}
        assert not (
            own_sequels & wrong
        ), "a wrong answer was one of the subject's own (genuine) sequels"
    assert seen_duplicate_subject, "sequel never picked the duplicated work"


def test_top_recommendation_declines_when_the_top_two_tie():
    # Alpha and Beta are tied at 100 -- with only 4 recommendations total there
    # is no way to sample around the tie, so every attempt must decline rather
    # than arbitrarily crown one of the tied pair "the most strongly
    # recommended" while marking the other one wrong.
    subject = {
        "title": "Tied Show",
        "recommendations": {"Alpha": 100, "Beta": 100, "Gamma": 50, "Delta": 10},
    }
    pool = [subject]
    tie_ctx = QuizContext(
        animes=pool,
        pool=pool,
        themes={},
        episodes={},
        characters_by_origin={},
        closeness=1.0,
    )
    for seed in range(60):
        q = ARCHETYPES["top_recommendation"].build(tie_ctx, random.Random(seed))
        assert q is None, (
            "top_recommendation must decline on an unbreakable tie, not silently "
            f"pick a winner (got {q!r})"
        )
