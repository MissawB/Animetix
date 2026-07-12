# backend/core/domain/services/world_boss/context.py
"""What an archetype is handed, and how it turns a fact into four options."""

import random
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

OPTIONS = 4
MASK = "▮▮▮"


@dataclass(frozen=True)
class Question:
    """`correct_index` is server-side only — it must never be serialised to a client."""

    archetype: str
    prompt: str
    options: List[str]
    correct_index: int
    subject: str  # the work the question is about, revealed after the answer
    image: Optional[str] = None  # only the cover archetype ships one


@dataclass(frozen=True)
class QuizContext:
    animes: List[Dict[str, Any]]  # the whole catalogue, most popular first
    pool: List[Dict[str, Any]]  # the works a question may be ABOUT, at this tier
    themes: Dict[str, Any]  # AniList id (str) -> {"title": ..., "themes": [...]}
    episodes: Dict[
        str, List[Dict[str, Any]]
    ]  # MAL id (str) -> [{number, title, synopsis}]
    characters_by_origin: Dict[str, List[Dict[str, Any]]]  # work title -> characters
    closeness: float  # 0 = far-fetched distractors, 1 = as close as the data allows


def title_of(item: Dict[str, Any]) -> str:
    return item.get("title") or item.get("name") or ""


def make_question(
    rng: random.Random,
    archetype: str,
    prompt: str,
    correct: str,
    distractors: Sequence[Any],
    subject: str,
    image: Optional[str] = None,
) -> Optional[Question]:
    """Four distinct options, the answer among them, in a random slot.

    Returns None when the data cannot field three usable distractors — the engine
    then retries with another archetype. A three-option question would quietly hand
    the player a 33 % floor.
    """
    correct = str(correct).strip()
    if not correct:
        return None

    seen = {correct.casefold()}
    usable: List[str] = []
    for value in distractors:
        text = str(value or "").strip()
        key = text.casefold()
        if not text or key in seen:
            continue
        seen.add(key)
        usable.append(text)

    if len(usable) < OPTIONS - 1:
        return None

    options = rng.sample(usable, OPTIONS - 1) + [correct]
    rng.shuffle(options)
    return Question(
        archetype=archetype,
        prompt=prompt,
        options=options,
        correct_index=options.index(correct),
        subject=subject,
        image=image,
    )


def mask_title(text: str, title: str) -> str:
    """Hide the work's own name inside a plot summary.

    Kitsu synopses routinely open with the title. Without this, the hardest
    archetype in the game would be the easiest one.
    """
    masked = text
    for word in re.split(r"[^\w]+", title):
        if len(word) < 4:
            continue
        masked = re.sub(rf"\b{re.escape(word)}\w*", MASK, masked, flags=re.IGNORECASE)
    return masked
