# backend/core/domain/services/world_boss/archetypes_relational.py
"""Bands C (expertise) and D (mastery).

Openings come from anime_themes.json, episodes from Kitsu, casts from the character
catalogue, and the rest from the recommendation graph the catalogue already carries.
Nothing here is generated: every answer and every distractor is a value some work
really holds.
"""

from typing import Any, Dict, List, Tuple

from .context import (
    QuizContext,
    episodes_of,
    make_question,
    mask_title,
    themes_of,
    title_of,
)
from .registry import archetype

SECONDARY_RANK = 200  # a character nobody puts on a poster


def _themed(ctx: QuizContext) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """(work, theme) for every work of the pool that has an opening on file.

    The lookup goes through `themes_of`: the JSON catalogue keys a work by its
    AniList id, the relational one by its MAL id, and neither archetype here has
    any business knowing which one it was handed.
    """
    pairs = []
    for work in ctx.pool:
        entry = themes_of(ctx, work)
        for theme in (entry or {}).get("themes", []):
            if theme.get("song_title"):
                pairs.append((work, theme))
    return pairs


def _all_themes(ctx: QuizContext) -> List[Dict[str, Any]]:
    # `ctx.themes` is indexed under SEVERAL keys per entry (AniList id and MAL id)
    # so a work can be resolved whichever id it carries. Walking `.values()` would
    # therefore see the same entry twice and double-weight its artists in the
    # distractor pool -- dedupe on identity.
    seen = set()
    songs = []
    for entry in ctx.themes.values():
        if id(entry) in seen:
            continue
        seen.add(id(entry))
        songs.extend(t for t in entry.get("themes", []) if t.get("song_title"))
    return songs


def _episoded(ctx: QuizContext) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    pairs = []
    for work in ctx.pool:
        for episode in episodes_of(ctx, work):
            pairs.append((work, episode))
    return pairs


def _cast(ctx: QuizContext, work: Dict[str, Any]) -> List[Dict[str, Any]]:
    return ctx.characters_by_origin.get(title_of(work), [])


def _rank(character: Dict[str, Any]) -> int:
    return (character.get("popularity") or {}).get("rank") or 9999


# ── Band C ────────────────────────────────────────────────────────────────────


@archetype("opening_to_work", {"C"})
def _opening_to_work(ctx, rng):
    pairs = _themed(ctx)
    if not pairs:
        return None
    work, theme = rng.choice(pairs)
    return make_question(
        rng,
        "opening_to_work",
        f"L'opening « {theme['song_title']} » appartient à quelle œuvre ?",
        title_of(work),
        [title_of(it) for it in ctx.pool if it is not work],
        subject=title_of(work),
    )


@archetype("shared_tag", {"C"})
def _shared_tag(ctx, rng):
    tagged = [it for it in ctx.pool if it.get("tags")]
    if len(tagged) < 2:
        return None
    for _ in range(12):
        first, second = rng.sample(tagged, 2)
        common = set(first["tags"]) & set(second["tags"])
        if not common:
            continue
        # The distractors are tags the FIRST work carries alone: knowing one of the
        # two works is not enough — you have to know both.
        only_first = set(first["tags"]) - set(second["tags"])
        elsewhere = {t for it in ctx.animes for t in it.get("tags") or []} - common
        return make_question(
            rng,
            "shared_tag",
            f"Quel tag « {title_of(first)} » et « {title_of(second)} » partagent-ils ?",
            rng.choice(sorted(common)),
            sorted(only_first) + sorted(elsewhere - only_first),
            subject=title_of(first),
        )
    return None


@archetype("not_recommended", {"C"})
def _not_recommended(ctx, rng):
    subjects = [it for it in ctx.pool if len(it.get("recommendations") or {}) >= 3]
    if not subjects:
        return None
    subject = rng.choice(subjects)
    recommended = list(subject["recommendations"])
    outsiders = [
        title_of(it)
        for it in ctx.pool
        if it is not subject and title_of(it) not in subject["recommendations"]
    ]
    if not outsiders:
        return None
    return make_question(
        rng,
        "not_recommended",
        f"Laquelle n'est PAS recommandée aux fans de « {title_of(subject)} » ?",
        rng.choice(outsiders),
        rng.sample(recommended, 3),
        subject=title_of(subject),
    )


@archetype("same_work_character", {"C"})
def _same_work_character(ctx, rng):
    duos = [it for it in ctx.pool if len(_cast(ctx, it)) >= 2]
    if not duos:
        return None
    work = rng.choice(duos)
    known, answer = rng.sample(_cast(ctx, work), 2)
    work_title = title_of(work)
    # Two guards, not one object-identity check: `_cast` keys on the work's
    # TITLE, so a duplicate-titled pool entry (a re-ingested season, a
    # franchise reusing its title) resolves to the SAME cast and `it is not
    # work` alone would let it back in as a "stranger". Restrict the pool by
    # title, and also check the character's own `origin` field as a
    # belt-and-suspenders pass.
    elsewhere = [
        title_of(c)
        for it in ctx.pool
        if title_of(it) != work_title
        for c in _cast(ctx, it)
        if c.get("origin") != work_title
    ]
    return make_question(
        rng,
        "same_work_character",
        # `title_of`, jamais `c["name"]` : servi par la base, un personnage porte
        # son nom sous `title` et n'a aucune clé `name` (cf. `_to_dict`).
        f"Quel personnage vient de la même œuvre que {title_of(known)} ?",
        title_of(answer),
        elsewhere,
        subject=title_of(work),
    )


@archetype("secondary_character", {"C"})
def _secondary_character(ctx, rng):
    candidates = [
        (it, c) for it in ctx.pool for c in _cast(ctx, it) if _rank(c) > SECONDARY_RANK
    ]
    if not candidates:
        return None
    work, character = rng.choice(candidates)
    work_title = title_of(work)
    # Same exploit `same_work_character` was fixed for: `_cast` keys on the
    # work's TITLE, so a duplicate-titled pool entry (a re-ingested season, a
    # franchise reusing its title) resolves to the SAME cast and `it is not
    # work` alone would let it back in as a "stranger". Restrict the pool by
    # title, and also check the character's own `origin` field as a
    # belt-and-suspenders pass.
    elsewhere = [
        title_of(c)
        for it in ctx.pool
        if title_of(it) != work_title
        for c in _cast(ctx, it)
        if c.get("origin") != work_title
    ]
    return make_question(
        rng,
        "secondary_character",
        f"Quel personnage secondaire apparaît dans « {title_of(work)} » ?",
        title_of(character),
        elsewhere,
        subject=title_of(work),
    )


@archetype("episode_title", {"C"})
def _episode_title(ctx, rng):
    pairs = [(w, e) for w, e in _episoded(ctx) if e.get("title")]
    if not pairs:
        return None
    work, episode = rng.choice(pairs)
    return make_question(
        rng,
        "episode_title",
        f"L'épisode {episode['number']} intitulé « {episode['title']} » appartient à quelle œuvre ?",
        title_of(work),
        [title_of(it) for it in ctx.pool if it is not work],
        subject=title_of(work),
    )


@archetype("sequel", {"C"})
def _sequel(ctx, rng):
    with_sequel = [it for it in ctx.pool if (it.get("relations") or {}).get("SEQUEL")]
    if len(with_sequel) < 4:
        return None
    subject = rng.choice(with_sequel)
    subject_title = title_of(subject)
    # Same exploit `same_work_character` / `secondary_character` were fixed
    # for: a duplicate-titled twin of `subject` (a re-ingested season, a
    # franchise reusing its title) can carry the identical multi-entry
    # `relations.SEQUEL` list. Excluding `subject` by object identity alone
    # would let that twin's entries -- which are the subject's OWN other
    # sequels -- leak in as "wrong" answers. Restrict by title instead.
    others = [
        s
        for it in with_sequel
        if title_of(it) != subject_title
        for s in it["relations"]["SEQUEL"]
    ]
    return make_question(
        rng,
        "sequel",
        f"Quelle œuvre est la suite directe de « {title_of(subject)} » ?",
        rng.choice(subject["relations"]["SEQUEL"]),
        others,
        subject=title_of(subject),
    )


@archetype("not_studio", {"C"})
def _not_studio(ctx, rng):
    studios = sorted({s for it in ctx.pool for s in it.get("studios") or []})
    rng.shuffle(studios)
    for studio in studios:
        theirs = [it for it in ctx.pool if studio in (it.get("studios") or [])]
        others = [it for it in ctx.pool if studio not in (it.get("studios") or [])]
        if len(theirs) < 3 or not others:
            continue
        odd = rng.choice(others)
        return make_question(
            rng,
            "not_studio",
            f"Laquelle de ces œuvres n'a PAS été animée par {studio} ?",
            title_of(odd),
            [title_of(it) for it in rng.sample(theirs, 3)],
            subject=title_of(odd),
        )
    return None


# ── Band D ────────────────────────────────────────────────────────────────────


@archetype("opening_artist", {"D"})
def _opening_artist(ctx, rng):
    pairs = [(w, t) for w, t in _themed(ctx) if t.get("artists")]
    if not pairs:
        return None
    work, theme = rng.choice(pairs)
    performer = theme["artists"][0]
    # A song can have several credited performers (the themes data carries
    # `artists: [...]` straight from AnimeThemes.moe, which credits every
    # performer of a duet). `_all_themes` walks every theme, including this
    # one, so filtering out only `performer` would let a co-performer of the
    # CORRECT song survive as a "wrong" answer while they genuinely perform
    # it too. Exclude the whole theme's own artist list, not just the one
    # named `correct`.
    own_artists = set(theme.get("artists") or [])
    elsewhere = [
        a
        for t in _all_themes(ctx)
        if t is not theme
        for a in t.get("artists") or []
        if a not in own_artists
    ]
    return make_question(
        rng,
        "opening_artist",
        f"Qui interprète « {theme['song_title']} », l'opening de « {title_of(work)} » ?",
        performer,
        elsewhere,
        subject=title_of(work),
    )


@archetype("exact_year", {"D"})
def _exact_year(ctx, rng):
    dated = [it for it in ctx.pool if it.get("year")]
    if not dated:
        return None
    subject = rng.choice(dated)
    year = int(subject["year"])
    # ±1 / ±2. There is no room left to guess by decade.
    return make_question(
        rng,
        "exact_year",
        f"En quelle année EXACTEMENT est sortie « {title_of(subject)} » ?",
        str(year),
        [str(year + o) for o in rng.sample([-2, -1, 1, 2], 3)],
        subject=title_of(subject),
    )


@archetype("top_recommendation", {"D"})
def _top_recommendation(ctx, rng):
    subjects = [it for it in ctx.pool if len(it.get("recommendations") or {}) >= 4]
    if not subjects:
        return None
    subject = rng.choice(subjects)
    recommended = subject["recommendations"]
    for _ in range(8):
        picks = rng.sample(sorted(recommended), 4)
        ranked = sorted(picks, key=lambda title: recommended[title], reverse=True)
        # A clear winner, or two options would tie for "the most strongly
        # recommended" while only one is marked correct -- the same guard
        # `most_popular` (archetypes_core.py) uses for the same reason.
        if recommended[ranked[0]] < recommended[ranked[1]] * 1.2:
            continue
        best = ranked[0]
        # All four ARE recommended. Only their ranking separates them.
        return make_question(
            rng,
            "top_recommendation",
            f"Ces 4 œuvres sont recommandées aux fans de « {title_of(subject)} ». "
            "Laquelle l'est le plus fortement ?",
            best,
            [p for p in picks if p != best],
            subject=title_of(subject),
        )
    return None


@archetype("rare_tag", {"D"})
def _rare_tag(ctx, rng):
    counts: Dict[str, int] = {}
    for it in ctx.animes:
        for tag in it.get("tags") or []:
            counts[tag] = counts.get(tag, 0) + 1
    rare = {t for t, n in counts.items() if n <= 3}
    subjects = [it for it in ctx.pool if rare & set(it.get("tags") or [])]
    if not subjects:
        return None
    subject = rng.choice(subjects)
    own = set(subject["tags"])
    return make_question(
        rng,
        "rare_tag",
        f"Quel tag rare porte « {title_of(subject)} » ?",
        rng.choice(sorted(rare & own)),
        sorted(rare - own),
        subject=title_of(subject),
    )


@archetype("episode_synopsis", {"D"})
def _episode_synopsis(ctx, rng):
    pairs = [(w, e) for w, e in _episoded(ctx) if e.get("synopsis")]
    if not pairs:
        return None
    work, episode = rng.choice(pairs)
    plot = mask_title(episode["synopsis"], title_of(work))
    return make_question(
        rng,
        "episode_synopsis",
        f"« {plot} » — de quelle œuvre cet épisode est-il tiré ?",
        title_of(work),
        [title_of(it) for it in ctx.pool if it is not work],
        subject=title_of(work),
    )


@archetype("character_sheet", {"D"})
def _character_sheet(ctx, rng):
    enrolled = [
        (it, c, org)
        for it in ctx.pool
        for c in _cast(ctx, it)
        for org in ((c.get("entities") or {}).get("organizations") or [])
    ]
    if not enrolled:
        return None
    work, character, organisation = rng.choice(enrolled)
    # Exclude by the character's FULL organisation set, not by the row's own
    # org: `enrolled` holds one row per (work, character, organisation), so a
    # character in several organisations surfaces on several rows. Filtering
    # on the row's org alone lets one of those other rows back in as a "wrong"
    # answer for an organisation the character genuinely also belongs to.
    elsewhere = [
        title_of(c)
        for it, c, org in enrolled
        if organisation not in ((c.get("entities") or {}).get("organizations") or [])
        and title_of(c) != title_of(character)
    ]
    return make_question(
        rng,
        "character_sheet",
        f"Quel personnage appartient à « {organisation} » ?",
        title_of(character),
        elsewhere,
        subject=title_of(work),
    )


@archetype("opening_range", {"D"})
def _opening_range(ctx, rng):
    pairs = [
        (w, t) for w, t in _themed(ctx) if (t.get("entries") or [{}])[0].get("episodes")
    ]
    if not pairs:
        return None
    work, theme = rng.choice(pairs)
    covered = theme["entries"][0]["episodes"]
    elsewhere = [
        (t["entries"] or [{}])[0].get("episodes")
        for t in _all_themes(ctx)
        if t.get("entries")
    ]
    return make_question(
        rng,
        "opening_range",
        f"Quels épisodes « {theme['song_title']} » couvre-t-il dans « {title_of(work)} » ?",
        covered,
        elsewhere,
        subject=title_of(work),
    )
