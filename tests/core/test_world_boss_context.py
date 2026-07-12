# tests/core/test_world_boss_context.py
"""A question is only as honest as its options: four distinct values, the right one
placed at random, and never a plot summary that spells out its own answer."""

import random

from core.domain.services.world_boss.context import (
    QuizContext,
    make_question,
    mask_title,
    title_of,
)


def _ctx(closeness=0.0):
    return QuizContext(
        animes=[],
        pool=[],
        themes={},
        episodes={},
        characters_by_origin={},
        closeness=closeness,
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
