# backend/core/domain/services/world_boss/context.py
"""What an archetype is handed, and how it turns a fact into four options."""

import random
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

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
    # MAL id (str) -> the SAME theme entry `themes` holds, derived below. Kept as
    # its OWN index rather than merged into `themes`: the two id spaces are both
    # plain integers and numerically overlap, so a merged dict would let a work's
    # MAL id resolve against a DIFFERENT work's AniList key whenever the numbers
    # happened to collide (see `themes_of`). Callers only ever hand us `themes` --
    # this derives itself so every existing call site keeps working unchanged.
    themes_by_mal: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.themes_by_mal and self.themes:
            by_mal: Dict[str, Any] = {}
            for entry in self.themes.values():
                mal_id = (entry or {}).get("mal_id")
                if mal_id:
                    by_mal[str(mal_id)] = entry
            if by_mal:
                object.__setattr__(self, "themes_by_mal", by_mal)


def title_of(item: Dict[str, Any]) -> str:
    return item.get("title") or item.get("name") or ""


# Une œuvre n'a pas le même identifiant selon l'adaptateur qui la sert :
#   * le JSON traité porte `id` = id AniList et `idMal` = id MAL ;
#   * la base relationnelle expose `id` = external_id = l'id MAL, plus (depuis
#     `sync_catalog`) `idMal` et `anilist_id` en métadonnées.
# Les épisodes sont indexés par id MAL : on essaie donc les clés de la plus
# spécifique à la plus probable, sans jamais forcer un archétype à connaître la
# forme du catalogue qu'on lui a tendu.
EPISODE_ID_KEYS = ("idMal", "mal_id", "id", "anilist_id")


def candidate_ids(item: Dict[str, Any], keys: Sequence[str]) -> List[str]:
    ids: List[str] = []
    for key in keys:
        value = item.get(key)
        if value is None or value == "":
            continue
        text = str(value)
        if text not in ids:
            ids.append(text)
    return ids


def _theme_ids_of(work: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """(id AniList, id MAL) de cette œuvre, chacun `None` si inconnu.

    Forme JSON : `id` = AniList, `idMal` = MAL -- toujours ensemble. Forme base
    (depuis le correctif de métadonnées de `sync_catalog`) : `id` = MAL
    (`external_id`) ; c'est la PRÉSENCE de `anilist_id` qui signale cette forme,
    `id` seul ne permettant pas de distinguer les deux espaces. Les lignes de
    base synchronisées avant ce correctif ne portent ni `idMal` ni
    `anilist_id` : `id` est alors le seul id disponible -- c'est bien de l'id
    MAL, mais rien sur la ligne ne le prouve, donc on l'essaie dans les deux
    espaces, comme le faisait déjà le prédécesseur de cette fonction
    (`THEME_ID_KEYS`) pour ce même cas dégradé.
    """
    anilist_id = work.get("anilist_id")
    mal_id = work.get("idMal") or work.get("mal_id")
    raw_id = work.get("id")

    if anilist_id is not None:
        # Forme base : `id` est confirmé côté MAL par la présence d'`anilist_id`.
        if mal_id is None:
            mal_id = raw_id
    elif mal_id is not None:
        # Forme JSON : `idMal` à côté de `id` => `id` est côté AniList.
        anilist_id = raw_id
    else:
        # Aucun signal : on essaie `id` dans les deux espaces.
        anilist_id = raw_id
        mal_id = raw_id

    def _norm(value: Any) -> Optional[str]:
        return str(value) if value not in (None, "") else None

    return _norm(anilist_id), _norm(mal_id)


def _theme_entry_belongs(entry: Dict[str, Any], mal_id: Optional[str]) -> bool:
    """Garde-fou supplémentaire : rejette une entrée dont le PROPRE `mal_id`
    contredit celui de l'œuvre qu'on résout -- le seul signal qui reste pour
    attraper une collision numérique entre les deux espaces d'id quand la forme
    de l'œuvre ne suffisait pas à l'exclure d'avance."""
    entry_mal = entry.get("mal_id")
    if entry_mal in (None, "") or mal_id is None:
        return True
    return str(entry_mal) == mal_id


def themes_of(ctx: "QuizContext", work: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """L'entrée d'openings de cette œuvre -- jamais celle d'une autre.

    `ctx.themes` est indexé par id AniList (les clés du fichier), `ctx.themes_by_mal`
    par le `mal_id` que porte chaque entrée : deux espaces disjoints, chacun
    consulté avec un id de son propre espace SEULEMENT. Les fusionner (ce qu'un
    correctif précédent faisait) laissait une œuvre sans entrée propre résoudre
    son id MAL contre la clé AniList d'une œuvre différente dès que les deux
    espaces se recoupaient numériquement -- une mauvaise réponse validée comme
    bonne. Un échec doit produire `None` : l'archétype décline alors et le
    moteur en tire un autre, ce qui est le comportement sûr.
    """
    anilist_id, mal_id = _theme_ids_of(work)

    if anilist_id is not None:
        entry = ctx.themes.get(anilist_id)
        if entry and _theme_entry_belongs(entry, mal_id):
            return entry

    if mal_id is not None:
        entry = ctx.themes_by_mal.get(mal_id)
        if entry and _theme_entry_belongs(entry, mal_id):
            return entry

    return None


def episodes_of(ctx: "QuizContext", work: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in candidate_ids(work, EPISODE_ID_KEYS):
        episodes = ctx.episodes.get(key)
        if episodes:
            return episodes
    return []


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
