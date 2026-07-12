# tests/core/test_world_boss_context.py
"""A question is only as honest as its options: four distinct values, the right one
placed at random, and never a plot summary that spells out its own answer."""

import random

from core.domain.services.world_boss.context import (
    MASK,
    make_question,
    mask_title,
    title_of,
)


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
