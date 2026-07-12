"""The balance of the World Boss quiz, pinned.

The exponential curve is its own anti-farm — grinding the low tiers is worth
nothing — and the Limiter Break damage cap is the one thing standing between a
good player and one-shotting a 100k boss.
"""

import pytest
from core.domain.services.world_boss.rules import (
    BOSS_TOTAL_HP,
    LIMITER_DAMAGE,
    LIMITER_STREAK,
    MAX_TIER,
    band_for,
    closeness_for,
    damage_for,
    next_tier,
    pool_size_for,
    timer_for,
)


def test_damage_doubles_every_tier():
    assert [damage_for(t) for t in range(1, 13)] == [
        1,
        2,
        4,
        8,
        16,
        32,
        64,
        128,
        256,
        512,
        1024,
        2048,
    ]


def test_a_perfect_climb_is_four_percent_of_the_boss():
    perfect = sum(damage_for(t) for t in range(1, MAX_TIER + 1))
    assert perfect == 4095
    assert perfect / BOSS_TOTAL_HP < 0.05


def test_grinding_the_low_tiers_is_worth_nothing():
    # Five tiers farmed forever = 31 damage. 0.03% of the boss.
    assert sum(damage_for(t) for t in range(1, 6)) == 31


def test_limiter_break_doubles_but_does_not_keep_doubling():
    # 2 * 2**(15-1) would be 32768 — a single question would gut the boss.
    assert damage_for(12, limiter_break=True) == LIMITER_DAMAGE == 4096
    assert damage_for(20, limiter_break=True) == LIMITER_DAMAGE


def test_ten_questions_in_limiter_break_is_a_feat_not_an_exploit():
    assert 10 * LIMITER_DAMAGE / BOSS_TOTAL_HP == pytest.approx(0.4096)


def test_bands_map_to_tiers():
    assert [band_for(t) for t in (1, 3)] == ["A", "A"]
    assert [band_for(t) for t in (4, 6)] == ["B", "B"]
    assert [band_for(t) for t in (7, 9)] == ["C", "C"]
    assert [band_for(t) for t in (10, 12)] == ["D", "D"]


def test_limiter_break_draws_from_the_hardest_band_whatever_the_tier():
    assert band_for(1, limiter_break=True) == "D"


def test_the_pool_widens_then_opens_completely():
    assert pool_size_for(1) == 50
    assert pool_size_for(5) == 150
    assert pool_size_for(8) == 300
    assert pool_size_for(12) == 300
    assert pool_size_for(12, limiter_break=True) is None  # the whole catalogue


def test_the_clock_tightens():
    assert timer_for(1) == 20
    assert timer_for(5) == 15
    assert timer_for(8) == 12
    assert timer_for(12) == 8
    assert timer_for(12, limiter_break=True) == 6


def test_distractors_close_in():
    assert closeness_for(1) == 0.0
    assert closeness_for(12) == 1.0
    assert closeness_for(1, limiter_break=True) == 1.0
    assert 0 < closeness_for(6) < 1


def test_the_ladder_stops_at_twelve():
    assert next_tier(1) == 2
    assert next_tier(MAX_TIER) == MAX_TIER


def test_five_correct_answers_open_the_limiter_break():
    assert LIMITER_STREAK == 5
