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
            raw_themes = self.catalog_service.repository.load_themes() or {}
        except Exception as e:  # a missing themes file must not cost us the game
            logger.warning("World Boss: themes unavailable (%s)", e)
            raw_themes = {}

        raw_episodes = self.catalog_service.get_anime_episodes() or {}
        themes = self._index_themes(raw_themes)
        episodes = self._index_episodes(raw_episodes, raw_themes)

        characters: Dict[str, List[Dict[str, Any]]] = {}
        cast_catalog = self.catalog_service.load_data("Character") or {}
        for character in cast_catalog.get("db", []):
            origin = character.get("origin")
            if origin:
                characters.setdefault(origin, []).append(character)

        self._cache = (animes, themes, episodes, characters)
        return self._cache

    @staticmethod
    def _index_themes(raw: Dict[str, Any]) -> Dict[str, Any]:
        """Les openings, retrouvables par l'id AniList ET par l'id MAL.

        `anime_themes.json` est indexé par id AniList et chaque entrée porte son
        `mal_id`. Or le catalogue relationnel n'a QUE l'id MAL (external_id) :
        indexé sur la seule clé source, aucun de ses works ne se retrouvait, et
        les 3 archétypes d'opening étaient muets en production.

        Les clés sources gagnent sur les alias MAL (`setdefault`) : les deux
        espaces d'ids sont numériques et peuvent se croiser, la clé explicite
        doit donc primer.
        """
        index: Dict[str, Any] = {str(key): entry for key, entry in raw.items()}
        for entry in raw.values():
            mal_id = (entry or {}).get("mal_id")
            if mal_id:
                index.setdefault(str(mal_id), entry)
        return index

    @staticmethod
    def _index_episodes(raw: Dict[str, Any], themes: Dict[str, Any]) -> Dict[str, Any]:
        """Les épisodes, retrouvables par l'id MAL (leur clé) ET par l'id AniList.

        Kitsu indexe par id MAL. Le pont vers l'id AniList, ce sont les entrées
        d'openings, qui portent les deux : `{anilist_id: {"mal_id": ...}}`.
        """
        index: Dict[str, Any] = {str(key): value for key, value in raw.items()}
        for source_id, entry in themes.items():
            mal_id = (entry or {}).get("mal_id")
            if mal_id and str(mal_id) in index:
                index.setdefault(str(source_id), index[str(mal_id)])
        return index

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
            question = self._draw(rng.choice(candidates), ctx, rng)
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
        fallback = self._draw(ARCHETYPES[fallback_name], ctx, rng)
        if fallback is None:
            raise GameLogicError("World Boss: the catalogue cannot field a question.")
        logger.warning("World Boss: tier %s fell back to `%s`.", tier, fallback_name)
        return fallback

    @staticmethod
    def _draw(archetype, ctx: QuizContext, rng: random.Random) -> Optional[Question]:
        """Tire une question — et traite un archétype qui EXPLOSE comme un
        archétype qui décline.

        Décliner (None) est normal : les données manquent. Lever, non : c'est un
        bug (un `KeyError: 'name'` sur un catalogue servi par la base a coûté un
        500 en pleine montée). On le hurle dans les logs — mais le joueur, lui,
        reçoit une autre question plutôt qu'une erreur serveur.

        `GameLogicError` n'est PAS avalée : c'est la façon dont le domaine dit
        « je ne peux pas », et la vue la traduit en 503.
        """
        try:
            return archetype.build(ctx, rng)
        except GameLogicError:
            raise
        except Exception:
            logger.exception(
                "World Boss: l'archétype `%s` a levé — c'est un BUG, pas un refus. "
                "Question redessinée pour ne pas casser la partie du joueur.",
                getattr(archetype, "name", archetype),
            )
            return None
