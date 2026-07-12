"""The balance of the World Boss quiz. Pure arithmetic — no data, no Django.

Difficulty rises on four axes at once: which archetype is drawn (the band), how
close the distractors sit (`closeness`), how obscure the work may be (the pool),
and how little time there is (the timer). The damage curve is exponential, which
is what makes a deep climb the only thing worth doing.
"""

from typing import Optional

MAX_TIER = 12
BOSS_TOTAL_HP = 100_000

LIMITER_STREAK = 5  # correct answers at MAX_TIER that open the Limiter Break
# Flat, NOT 2 * 2**(tier-1): left to keep doubling, one question past tier 15 would
# deal 32768 and gut a 100k boss on its own. Difficulty stays unbounded; reward does not.
LIMITER_DAMAGE = 4096
LIMITER_TIMER = 6

GRACE_SECONDS = 2.0  # network latency; beyond it, an answer is late

# band -> (last tier of the band, pool size, timer in seconds)
_BANDS = (
    ("A", 3, 50, 20),
    ("B", 6, 150, 15),
    ("C", 9, 300, 12),
    ("D", MAX_TIER, 300, 8),
)


def _row(tier: int):
    for row in _BANDS:
        if tier <= row[1]:
            return row
    return _BANDS[-1]


def band_for(tier: int, limiter_break: bool = False) -> str:
    """In Limiter Break every question is drawn from the hardest band."""
    return "D" if limiter_break else _row(tier)[0]


def pool_size_for(tier: int, limiter_break: bool = False) -> Optional[int]:
    """How many works (most popular first) a question may be about. None = all of them."""
    return None if limiter_break else _row(tier)[2]


def timer_for(tier: int, limiter_break: bool = False) -> int:
    return LIMITER_TIMER if limiter_break else _row(tier)[3]


def damage_for(tier: int, limiter_break: bool = False) -> int:
    return LIMITER_DAMAGE if limiter_break else 2 ** (tier - 1)


def closeness_for(tier: int, limiter_break: bool = False) -> float:
    """0 = distractors are obviously wrong, 1 = as close to the answer as the data allows.

    The least visible of the four axes, and the strongest: 2019 against 1998 is a
    different game from 2019 against 2018.
    """
    if limiter_break:
        return 1.0
    return (min(tier, MAX_TIER) - 1) / (MAX_TIER - 1)


def next_tier(tier: int) -> int:
    """The ladder stops at 12; past it, the Limiter Break takes over."""
    return min(tier + 1, MAX_TIER)
