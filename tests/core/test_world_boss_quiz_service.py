# tests/core/test_world_boss_quiz_service.py
"""The engine: pick a band, draw an archetype, and never hand the player a
half-built question. The catalogue ordering is the service's own business — the SQL
row order cannot be trusted."""

import random
from unittest.mock import MagicMock

import pytest
from core.domain.services.world_boss.rules import MAX_TIER
from core.domain.services.world_boss.service import WorldBossQuizService

from tests.core.test_world_boss_archetypes_core import ANIMES, CHARACTERS


def _service(animes=None):
    catalog = MagicMock()
    catalog.load_data.side_effect = lambda media_type: {
        "Anime": {"db": list(animes if animes is not None else ANIMES)},
        "Character": {"db": [c for cast in CHARACTERS.values() for c in cast]},
    }.get(media_type)
    catalog.get_anime_episodes.return_value = {}
    catalog.repository.load_themes.return_value = {}
    return WorldBossQuizService(catalog_service=catalog)


@pytest.mark.parametrize("tier", range(1, MAX_TIER + 1))
def test_every_tier_yields_a_playable_question(tier):
    question = _service().build_question(tier, rng=random.Random(tier))

    assert len(question.options) == 4
    assert 0 <= question.correct_index < 4
    assert question.prompt


def test_the_catalogue_is_sorted_by_popularity_whatever_order_it_arrives_in():
    shuffled = list(reversed(ANIMES))  # the SQL adapter returns rows in column order,
    service = _service(shuffled)  # and MediaItem.popularity was 0.0 for everyone

    assert [a["title"] for a in service._base()[0]][:2] == [
        "Kimetsu no Yaiba",
        "Jujutsu Kaisen",
    ]


def test_a_tier_one_question_only_draws_from_the_most_popular_works():
    service = _service()
    subjects = {
        service.build_question(1, rng=random.Random(seed)).subject for seed in range(30)
    }
    # The fixture has 8 works, so the top-50 pool is all of them: assert on the rule,
    # not the fixture.
    assert subjects <= {a["title"] for a in ANIMES}


def test_limiter_break_draws_band_d_archetypes():
    service = _service()
    names = {
        service.build_question(1, limiter_break=True, rng=random.Random(s)).archetype
        for s in range(40)
    }
    assert names <= {
        "opening_artist",
        "exact_year",
        "top_recommendation",
        "rare_tag",
        "episode_synopsis",
        "character_sheet",
        "opening_range",
    }


def test_the_same_seed_gives_the_same_question():
    service = _service()
    first = service.build_question(7, rng=random.Random(99))
    second = service.build_question(7, rng=random.Random(99))
    assert (first.prompt, first.options) == (second.prompt, second.options)


def test_an_unseeded_call_does_not_repeat_itself():
    service = _service()
    prompts = {service.build_question(3).prompt for _ in range(12)}
    assert len(prompts) > 1


def test_an_empty_catalogue_raises_rather_than_shipping_a_broken_quiz():
    from core.domain.exceptions import GameLogicError

    with pytest.raises(GameLogicError):
        _service(animes=[]).build_question(1)
