# tests/core/test_world_boss_context.py
"""A question is only as honest as its options: four distinct values, the right one
placed at random, and never a plot summary that spells out its own answer."""

import json
import random
from pathlib import Path

import pytest
from core.domain.services.world_boss.context import (
    MASK,
    QuizContext,
    make_question,
    mask_title,
    themes_of,
    title_of,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
THEMES_FILE = REPO_ROOT / "data" / "processed" / "anime_themes.json"
ANIMES_FILE = REPO_ROOT / "data" / "processed" / "clean_root_animes.json"

_LFS_POINTER = "version https://git-lfs"


def _load_real_data_or_skip(path: Path):
    """The catalogue files are tracked with Git LFS. CI checks out the pointers
    without fetching the objects, so `path.exists()` is true while the content is
    a 130-byte text stub -- json.load then dies on 'Expecting value: line 1'.
    Skip on the stub instead of failing: this is a guard on the live data, and a
    checkout that has no live data has nothing to guard."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if text.startswith(_LFS_POINTER):
        pytest.skip(f"{path.name} is an unfetched Git LFS pointer")
    return json.loads(text)


def test_the_answer_is_not_always_in_the_same_slot():
    slots = {
        make_question(
            random.Random(seed),
            "year",
            "Quand ?",
            "2019",
            ["2018", "2020", "2021"],
            subject="X",
        ).correct_index
        for seed in range(40)
    }
    assert len(slots) > 1


def test_the_option_at_the_correct_index_is_the_answer():
    q = make_question(
        random.Random(3),
        "year",
        "Quand ?",
        "2019",
        ["2018", "2020", "2021"],
        subject="X",
    )
    assert q.options[q.correct_index] == "2019"
    assert len(q.options) == 4


def test_duplicate_and_empty_distractors_are_dropped():
    q = make_question(
        random.Random(3),
        "year",
        "Quand ?",
        "2019",
        ["2018", "2018", "", None, "2020", "2021"],
        subject="X",
    )
    assert sorted(q.options) == ["2018", "2019", "2020", "2021"]


def test_a_question_that_cannot_field_four_options_is_refused():
    # The engine retries with another archetype rather than shipping a 3-option quiz.
    assert (
        make_question(
            random.Random(3), "year", "Quand ?", "2019", ["2018"], subject="X"
        )
        is None
    )


def test_a_distractor_equal_to_the_answer_is_dropped():
    assert (
        make_question(
            random.Random(3),
            "year",
            "Quand ?",
            "2019",
            ["2019", "2018", "2020"],
            subject="X",
        )
        is None
    )


def test_a_falsy_but_valid_distractor_is_kept():
    # 0 (an episode number, a count...) must not be treated as empty.
    q = make_question(
        random.Random(3),
        "episode_count",
        "Combien ?",
        "5",
        [0, 1, 2],
        subject="X",
    )
    assert q is not None
    assert "0" in q.options


def test_a_distractor_differing_only_in_case_is_dropped_as_duplicate():
    q = make_question(
        random.Random(3),
        "character",
        "Qui ?",
        "Naruto",
        ["naruto", "Sasuke", "Sakura", "Kakashi"],
        subject="X",
    )
    assert q is not None
    assert sorted(q.options) == sorted(["Naruto", "Sasuke", "Sakura", "Kakashi"])
    assert "naruto" not in q.options


def test_a_plot_summary_never_spells_out_its_own_answer():
    masked = mask_title(
        "Tanjiro Kamado joins the Demon Slayer Corps after his family is killed.",
        "Kimetsu no Yaiba: Demon Slayer",
    )
    assert "Demon" not in masked
    assert "Slayer" not in masked
    assert "Tanjiro" in masked  # only the title is hidden, not the story


def test_title_of_falls_back_to_name():
    assert title_of({"title": "Berserk"}) == "Berserk"
    assert title_of({"name": "Levi"}) == "Levi"
    assert title_of({}) == ""


def test_mask_title_masks_a_title_whose_words_are_all_below_the_length_floor():
    # "K-On!" -> words "K" and "On", both shorter than the length-4 floor. Without
    # a fallback, the guard that keeps ordinary short prose intact also skips the
    # title itself, and the synopsis ships with its own answer spelled out.
    text = "K-On! follows a group of girls in the light music club."
    masked = mask_title(text, "K-On!")
    assert masked != text
    assert MASK in masked
    assert "k-on" not in masked.lower()


def test_mask_title_handles_regex_metacharacters_without_raising():
    cases = {
        "Steins;Gate": "Steins;Gate follows a lab member who alters the past by text messages.",
        "Fate/Zero": "Fate/Zero depicts a war between mages and their servants.",
    }
    for title, text in cases.items():
        masked = mask_title(text, title)
        assert MASK in masked
        for word in title.replace(";", " ").replace("/", " ").split():
            assert word.lower() not in masked.lower()


# `themes_of` resolves a work's opening whichever catalogue shape served it:
#   * the JSON file: `id` = id AniList, `idMal` = id MAL;
#   * the relational DB adapter (post `sync_catalog` metadata fix): `id` = the
#     external_id = id MAL, plus `anilist_id` and `idMal` in metadata.
# `anime_themes.json` is keyed by id AniList and covers only a slice of the
# catalogue: a work outside that slice has no entry of its own. The two id
# spaces are both plain integers and numerically overlap -- nothing stops a
# work's MAL id from equalling a DIFFERENT work's AniList id.


def test_themes_of_never_lets_a_missing_works_mal_id_resolve_a_strangers_anilist_entry():
    # Haikyuu!! has its own opening, keyed by ITS AniList id (20583). Rail
    # Wars!'s real MAL id (23309) is a DIFFERENT number in real data, but here
    # we pin the exact collision shape: Rail Wars!'s MAL id is numerically
    # identical to Haikyuu!!'s AniList key. Rail Wars! has NO theme entry of
    # its own -- resolving it must never borrow Haikyuu!!'s by that collision.
    themes = {
        "20583": {
            "title": "Haikyuu!!",
            "mal_id": 20464,  # Haikyuu!!'s OWN (different) MAL id
            "themes": [
                {"type": "OP", "song_title": "Imagination", "artists": ["SPYAIR"]}
            ],
        },
    }
    rail_wars_db_shape = {
        "id": "20583",  # Rail Wars!'s external_id -- its MAL id, in DB shape
        "idMal": "20583",
        "anilist_id": "20488",  # Rail Wars!'s OWN, real, AniList id
        "title": "Rail Wars!",
    }
    ctx = QuizContext(
        animes=[rail_wars_db_shape],
        pool=[rail_wars_db_shape],
        themes=themes,
        episodes={},
        characters_by_origin={},
        closeness=1.0,
    )

    assert themes_of(ctx, rail_wars_db_shape) is None


def test_themes_of_still_resolves_a_works_own_theme_in_both_catalogue_shapes():
    entry = {
        "title": "Kimetsu no Yaiba",
        "mal_id": 38000,
        "themes": [{"type": "OP", "song_title": "Gurenge", "artists": ["LiSA"]}],
    }
    themes = {"101922": entry}

    json_shape = {"id": 101922, "idMal": 38000, "title": "Kimetsu no Yaiba"}
    db_shape = {
        "id": "38000",
        "idMal": "38000",
        "anilist_id": "101922",
        "title": "Kimetsu no Yaiba",
    }
    ctx = QuizContext(
        animes=[json_shape, db_shape],
        pool=[json_shape, db_shape],
        themes=themes,
        episodes={},
        characters_by_origin={},
        closeness=1.0,
    )

    assert themes_of(ctx, json_shape) is entry
    assert themes_of(ctx, db_shape) is entry


def test_themes_of_never_mis_attributes_against_the_real_catalogue():
    """A guard on the live data, not just a hand-built fixture. 2155 works,
    200 theme entries -- small enough to run on every test invocation.

    For every work in `clean_root_animes.json`, whatever `themes_of` resolves
    must genuinely be ITS OWN entry: keyed by its own AniList id, or carrying
    its own MAL id as `mal_id`. Exercised in both catalogue shapes (JSON as
    shipped, and the DB shape a synced work presents) so a regression in
    either resolution path is caught here, not by a player losing their climb.
    """
    if not THEMES_FILE.exists() or not ANIMES_FILE.exists():
        pytest.skip("real catalogue data files are not present in this checkout")

    themes = _load_real_data_or_skip(THEMES_FILE)
    animes = _load_real_data_or_skip(ANIMES_FILE)

    resolved = 0
    misattributed = []

    for anime in animes:
        anilist_id = anime.get("id")
        mal_id = anime.get("idMal")

        for work in (
            {"id": anilist_id, "idMal": mal_id, "title": anime.get("title")},  # JSON
            {
                "id": str(mal_id),
                "idMal": str(mal_id),
                "anilist_id": str(anilist_id),
                "title": anime.get("title"),
            },  # DB, post `sync_catalog` metadata fix
        ):
            ctx = QuizContext(
                animes=[work],
                pool=[work],
                themes=themes,
                episodes={},
                characters_by_origin={},
                closeness=1.0,
            )
            entry = themes_of(ctx, work)
            if entry is None:
                continue
            resolved += 1
            entry_mal = entry.get("mal_id")
            belongs = (
                str(anilist_id) in themes and themes[str(anilist_id)] is entry
            ) or (entry_mal is not None and str(entry_mal) == str(mal_id))
            if not belongs:
                misattributed.append((anime.get("title"), anilist_id, mal_id))

    assert not misattributed, f"mis-attributed openings: {misattributed}"
    assert resolved > 0, "the guard resolved nothing at all -- data files likely moved"
