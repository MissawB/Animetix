from . import archetypes_core, archetypes_relational  # noqa: F401  (registers them)
from .context import Question, QuizContext  # noqa: F401
from .registry import ARCHETYPES, archetypes_for  # noqa: F401
from .rules import (  # noqa: F401
    BOSS_TOTAL_HP,
    GRACE_SECONDS,
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
from .service import WorldBossQuizService  # noqa: F401
