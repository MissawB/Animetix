# backend/core/domain/services/world_boss/archetypes_core.py
"""Bands A (recognition) and B (knowledge).

Band A asks what anyone who watched the work knows. Band B asks what someone who
follows the medium knows. Neither needs the relation graph — that is bands C and D.
"""

import random
from typing import Any, Dict, List, Optional

from .context import Question, QuizContext, make_question, title_of
from .registry import archetype

SOURCE_LABELS = {
    "MANGA": "Un manga",
    "LIGHT_NOVEL": "Un light novel",
    "NOVEL": "Un roman",
    "VISUAL_NOVEL": "Un visual novel",
    "VIDEO_GAME": "Un jeu vidéo",
    "ORIGINAL": "Une création originale",
    "WEB_NOVEL": "Un web novel",
    "DOUJINSHI": "Un doujinshi",
    "OTHER": "Autre chose",
}


def _with(ctx: QuizContext, key: str) -> List[Dict[str, Any]]:
    """The works in the current pool that actually carry `key`."""
    return [it for it in ctx.pool if it.get(key)]


def _others(ctx: QuizContext, subject: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [it for it in ctx.pool if it is not subject]


def _year_race(
    ctx: QuizContext,
    rng: random.Random,
    name: str,
    prompt: str,
    min_gap: int,
    max_gap: int,
) -> Optional[Question]:
    """Four works, distinct years; the gap between the two oldest sets the difficulty."""
    dated = _with(ctx, "year")
    if len(dated) < 4:
        return None
    for _ in range(8):
        picks = rng.sample(dated, 4)
        years = sorted(int(it["year"]) for it in picks)
        if len(set(years)) < 4 or not (min_gap <= years[1] - years[0] <= max_gap):
            continue
        oldest = min(picks, key=lambda it: int(it["year"]))
        return make_question(
            rng,
            name,
            prompt,
            title_of(oldest),
            [title_of(it) for it in picks if it is not oldest],
            subject=title_of(oldest),
        )
    return None


# ── Band A ────────────────────────────────────────────────────────────────────


@archetype("year", {"A"})
def _year(ctx, rng):
    dated = _with(ctx, "year")
    if not dated:
        return None
    subject = rng.choice(dated)
    year = int(subject["year"])
    # Distractors are generated as year +/- offset rather than lifted from other
    # works' real years: only a generated value can guarantee the tight +/-2
    # window tier 12 demands. Sibling works' actual years are whatever the
    # catalogue happens to contain and cannot be relied on to cluster that close.
    # 12 years apart at tier 1, 2 at tier 12: the same question, four times harder.
    window = max(2, round(12 - 10 * ctx.closeness))
    offsets = rng.sample([o for o in range(-window, window + 1) if o], 3)
    return make_question(
        rng,
        "year",
        f"En quelle année est sortie « {title_of(subject)} » ?",
        str(year),
        [str(year + o) for o in offsets],
        subject=title_of(subject),
    )


@archetype("genre", {"A"})
def _genre(ctx, rng):
    subjects = _with(ctx, "genres")
    if not subjects:
        return None
    subject = rng.choice(subjects)
    every = {g for it in ctx.animes for g in it.get("genres") or []}
    return make_question(
        rng,
        "genre",
        f"Quel genre correspond à « {title_of(subject)} » ?",
        rng.choice(subject["genres"]),
        sorted(every - set(subject["genres"])),
        subject=title_of(subject),
    )


@archetype("cover", {"A"})
def _cover(ctx, rng):
    subjects = [it for it in ctx.pool if it.get("image") and title_of(it)]
    if len(subjects) < 4:
        return None
    subject = rng.choice(subjects)
    return make_question(
        rng,
        "cover",
        "Quelle œuvre cette jaquette annonce-t-elle ?",
        title_of(subject),
        [title_of(it) for it in _others(ctx, subject)],
        subject=title_of(subject),
        image=subject["image"],
    )


@archetype("most_popular", {"A"})
def _most_popular(ctx, rng):
    known = _with(ctx, "popularity")
    if len(known) < 4:
        return None
    for _ in range(8):
        picks = rng.sample(known, 4)
        ranked = sorted(picks, key=lambda it: it["popularity"], reverse=True)
        # A clear winner, or the question is a coin toss dressed up as knowledge.
        if ranked[0]["popularity"] < ranked[1]["popularity"] * 1.2:
            continue
        return make_question(
            rng,
            "most_popular",
            "Laquelle de ces œuvres est la plus populaire ?",
            title_of(ranked[0]),
            [title_of(it) for it in ranked[1:]],
            subject=title_of(ranked[0]),
        )
    return None


@archetype("oldest", {"A"})
def _oldest(ctx, rng):
    return _year_race(
        ctx,
        rng,
        "oldest",
        "Laquelle de ces œuvres est la plus ancienne ?",
        min_gap=4,
        max_gap=100,
    )


# ── Band B ────────────────────────────────────────────────────────────────────


@archetype("tag", {"B"})
def _tag(ctx, rng):
    subjects = _with(ctx, "tags")
    if not subjects:
        return None
    subject = rng.choice(subjects)
    own = set(subject["tags"])
    # Close in: past mid-ladder the wrong tags come from works of the same genre.
    neighbours = ctx.animes
    if ctx.closeness >= 0.3 and subject.get("genres"):
        same_genre = [
            it
            for it in ctx.animes
            if set(it.get("genres") or []) & set(subject["genres"])
        ]
        neighbours = same_genre or ctx.animes
    elsewhere = {t for it in neighbours for t in it.get("tags") or []} - own
    return make_question(
        rng,
        "tag",
        f"Quel tag caractérise « {title_of(subject)} » ?",
        rng.choice(subject["tags"]),
        sorted(elsewhere),
        subject=title_of(subject),
    )


@archetype("character_origin", {"B"})
def _character_origin(ctx, rng):
    # `subjects` only needs a character to ask about; the four options come from
    # the whole pool via `_others`, so the pool -- not `subjects` -- must reach 4.
    subjects = [it for it in ctx.pool if ctx.characters_by_origin.get(title_of(it))]
    if not subjects or len(ctx.pool) < 4:
        return None
    subject = rng.choice(subjects)
    cast = ctx.characters_by_origin[title_of(subject)]
    star = max(cast, key=lambda c: (c.get("popularity") or {}).get("favourites", 0))
    return make_question(
        rng,
        "character_origin",
        f"Dans quelle œuvre apparaît {star['name']} ?",
        title_of(subject),
        [title_of(it) for it in _others(ctx, subject)],
        subject=title_of(subject),
    )


@archetype("recommended", {"B"})
def _recommended(ctx, rng):
    subjects = _with(ctx, "recommendations")
    if not subjects:
        return None
    subject = rng.choice(subjects)
    recommended = subject["recommendations"]
    best = max(recommended, key=recommended.get)
    unrelated = [
        title_of(it) for it in _others(ctx, subject) if title_of(it) not in recommended
    ]
    return make_question(
        rng,
        "recommended",
        f"Quelle œuvre est recommandée aux fans de « {title_of(subject)} » ?",
        best,
        unrelated,
        subject=title_of(subject),
    )


@archetype("released_first", {"B"})
def _released_first(ctx, rng):
    return _year_race(
        ctx,
        rng,
        "released_first",
        "Laquelle de ces œuvres est sortie en premier ?",
        min_gap=1,
        max_gap=3,
    )


@archetype("source", {"B"})
def _source(ctx, rng):
    subjects = [it for it in ctx.pool if it.get("source") in SOURCE_LABELS]
    if not subjects:
        return None
    subject = rng.choice(subjects)
    correct = SOURCE_LABELS[subject["source"]]
    # Distractors come from the closed SOURCE_LABELS vocabulary rather than from
    # other works' fields -- every label names a real, legitimate source category,
    # so any label other than the correct one is an honest wrong answer.
    return make_question(
        rng,
        "source",
        f"De quoi « {title_of(subject)} » est-il adapté ?",
        correct,
        [label for label in SOURCE_LABELS.values() if label != correct],
        subject=title_of(subject),
    )


@archetype("studio", {"B"})
def _studio(ctx, rng):
    subjects = _with(ctx, "studios")
    if not subjects:
        return None
    subject = rng.choice(subjects)
    own = set(subject["studios"])
    elsewhere = {s for it in ctx.animes for s in it.get("studios") or []} - own
    return make_question(
        rng,
        "studio",
        f"Quel studio a animé « {title_of(subject)} » ?",
        subject["studios"][0],
        sorted(elsewhere),
        subject=title_of(subject),
    )


@archetype("not_genre", {"B"})
def _not_genre(ctx, rng):
    genres = sorted({g for it in ctx.pool for g in it.get("genres") or []})
    rng.shuffle(genres)
    for genre in genres:
        having = [it for it in ctx.pool if genre in (it.get("genres") or [])]
        lacking = [it for it in ctx.pool if genre not in (it.get("genres") or [])]
        if len(having) < 3 or not lacking:
            continue
        odd = rng.choice(lacking)
        return make_question(
            rng,
            "not_genre",
            f"Laquelle de ces œuvres n'est PAS un « {genre} » ?",
            title_of(odd),
            [title_of(it) for it in rng.sample(having, 3)],
            subject=title_of(odd),
        )
    return None
