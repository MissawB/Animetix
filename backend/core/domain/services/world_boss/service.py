# backend/core/domain/services/world_boss/service.py
"""Draws a World Boss question. Pure: it reads the catalogue and nothing else."""

import logging
import random
import secrets
from typing import Any, Dict, List, Optional, Tuple

from ...exceptions import GameLogicError
from .context import Question, QuizContext, title_of
from .registry import ARCHETYPES, archetypes_for
from .rules import band_for, closeness_for, pool_size_for

logger = logging.getLogger("animetix.worldboss")

ATTEMPTS = 12  # an archetype declines when its data is missing; try another


class WorldBossQuizService:
    def __init__(self, catalog_service):
        self.catalog_service = catalog_service
        self._cache: Optional[Tuple[List[Dict], Dict, Dict, Dict]] = None

    def _base(self):
        """(animes sorted by popularity, themes, episodes, characters by origin)."""
        if self._cache is not None:
            return self._cache

        catalog = self.catalog_service.load_data("Anime") or {}
        # Sort here rather than trusting the row order: the catalogue can arrive from
        # the SQL adapter, and `order_by("-popularity")` there is only as good as the
        # popularity column.
        animes = sorted(
            (it for it in catalog.get("db", []) if title_of(it)),
            key=lambda it: it.get("popularity") or 0,
            reverse=True,
        )

        try:
            themes = self.catalog_service.repository.load_themes() or {}
        except Exception as e:  # a missing themes file must not cost us the game
            logger.warning("World Boss: themes unavailable (%s)", e)
            themes = {}

        episodes = self.catalog_service.get_anime_episodes() or {}

        characters: Dict[str, List[Dict[str, Any]]] = {}
        cast_catalog = self.catalog_service.load_data("Character") or {}
        for character in cast_catalog.get("db", []):
            origin = character.get("origin")
            if origin:
                characters.setdefault(origin, []).append(character)

        self._cache = (animes, themes, episodes, characters)
        return self._cache

    def _context(self, tier: int, limiter_break: bool) -> QuizContext:
        animes, themes, episodes, characters = self._base()
        size = pool_size_for(tier, limiter_break)
        return QuizContext(
            animes=animes,
            pool=animes[:size] if size else animes,
            themes=themes,
            episodes=episodes,
            characters_by_origin=characters,
            closeness=closeness_for(tier, limiter_break),
        )

    def build_question(
        self,
        tier: int,
        limiter_break: bool = False,
        rng: Optional[random.Random] = None,
    ) -> Question:
        """Draw one question for this tier.

        The seed is unguessable by default: a player who could predict the draw could
        pre-compute the ladder.
        """
        rng = rng or random.Random(secrets.randbits(64))
        band = band_for(tier, limiter_break)
        ctx = self._context(tier, limiter_break)
        candidates = archetypes_for(band)

        for _ in range(ATTEMPTS):
            question = rng.choice(candidates).build(ctx, rng)
            if question:
                return question

        # Every archetype in the band drew a blank: fall back on the one fact the
        # catalogue always has. In bands C/D (and Limiter Break) the fallback must
        # still be asked at the band's own difficulty -- handing out `year` (Band A)
        # here would let a data-starved catalogue collect Limiter Break's 4096
        # damage for the easiest question in the game. `exact_year` rests on the
        # same guaranteed `year` field, just with tighter (+/-1/+/-2) distractors.
        hard_band = band in ("C", "D") or limiter_break
        fallback_name = "exact_year" if hard_band else "year"
        fallback = ARCHETYPES[fallback_name].build(ctx, rng)
        if fallback is None:
            raise GameLogicError("World Boss: the catalogue cannot field a question.")
        logger.warning("World Boss: tier %s fell back to `%s`.", tier, fallback_name)
        return fallback
