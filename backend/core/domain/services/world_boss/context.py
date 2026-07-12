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
        if value is None:
            continue
        text = str(value).strip()
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

    Words of length >= 4 are masked individually so ordinary prose (short common
    words the title happens to share, e.g. "no") stays readable. If NONE of the
    title's words reach that floor -- e.g. "K-On!" splits into "K" and "On" --
    that guard would make the whole function a no-op and leak the answer, so we
    fall back to masking every word of the title however short. The full title
    is also masked as a single phrase (tolerating punctuation/whitespace between
    its words) as a belt-and-suspenders pass for runs the word-by-word loop
    could miss.
    """
    masked = text
    words = [word for word in re.split(r"[^\w]+", title) if word]
    long_words = [word for word in words if len(word) >= 4]

    # Over-masking a short-titled work's synopsis is acceptable; leaking its
    # answer is not -- so when no word clears the floor, mask them all anyway.
    for word in long_words or words:
        masked = re.sub(rf"\b{re.escape(word)}\w*", MASK, masked, flags=re.IGNORECASE)

    if words:
        phrase = r"[^\w]*".join(re.escape(word) for word in words)
        masked = re.sub(phrase, MASK, masked, flags=re.IGNORECASE)

    return masked
