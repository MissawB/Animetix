# backend/core/domain/services/world_boss/registry.py
"""The archetype registry.

A tier does not map to a question type — it maps to a BAND, and the band draws at
random from its pool of archetypes. Two climbs never look alike, and adding a
question type is a decorator, not a new branch in the engine.
"""

import random
from dataclasses import dataclass
from typing import Callable, Dict, FrozenSet, Iterable, List, Optional

from .context import Question, QuizContext

Builder = Callable[[QuizContext, random.Random], Optional[Question]]


@dataclass(frozen=True)
class Archetype:
    name: str
    bands: FrozenSet[str]
    build: Builder


ARCHETYPES: Dict[str, Archetype] = {}


def archetype(name: str, bands: Iterable[str]) -> Callable[[Builder], Builder]:
    """Register a builder. It returns None when its data is missing — never a guess."""

    def decorator(fn: Builder) -> Builder:
        ARCHETYPES[name] = Archetype(name=name, bands=frozenset(bands), build=fn)
        return fn

    return decorator


def archetypes_for(band: str) -> List[Archetype]:
    return sorted(
        (a for a in ARCHETYPES.values() if band in a.bands), key=lambda a: a.name
    )
