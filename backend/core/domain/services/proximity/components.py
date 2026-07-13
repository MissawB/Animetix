"""Les quatre composantes de la proximité entre deux œuvres.

Ce qu'on remplace : l'embedding de la description. Mesuré sur le vrai catalogue,
son plancher de bruit est à 0,583 entre deux œuvres SANS RAPPORT, et il classait
Kimetsu (0,671) plus proche de Death Note que Monster (0,654). Un synopsis d'anime,
c'est du vocabulaire d'anime.

Ce qu'on met à la place : le graphe de recommandations AniList — du jugement humain
agrégé — plus des tags pondérés par leur rareté. Chaque composante est nommée parce
qu'elle sera montrée au joueur.
"""

import math
from dataclasses import dataclass
from typing import Any, Dict, List

W_DIRECT = 0.45
W_CO_RECO = 0.30
W_TAGS = 0.25
BONUS_CAP = 0.15

# Une recommandation très votée (Death Note -> Code Geass) plafonne autour de 3500
# votes ; on normalise sur cet ordre de grandeur plutôt que sur le max du catalogue,
# qui bougerait à chaque ingestion.
_MAX_VOTES = math.log1p(4000)

_BONUS_STUDIO = 0.04
_BONUS_SOURCE = 0.02
_BONUS_DECADE = 0.01


@dataclass(frozen=True)
class ProximityIndex:
    works: Dict[str, Dict[str, Any]]  # titre -> œuvre
    reco: Dict[str, Dict[str, float]]  # titre -> {titre recommandé: log1p(votes)}
    idf: Dict[str, float]  # tag -> rareté


@dataclass(frozen=True)
class Components:
    direct: float
    co_reco: float
    tags: float
    bonus: float

    def total(self) -> float:
        base = W_DIRECT * self.direct + W_CO_RECO * self.co_reco + W_TAGS * self.tags
        # Le bonus ne PORTE jamais un score À LUI SEUL : sans signal de fond, il
        # vaut zéro. Deux œuvres sans rapport du même studio ne doivent pas
        # remonter. Exception unique : un bonus au PLAFOND (BONUS_CAP) ne vient
        # jamais d'une coïncidence structurelle (studio/source/décennie ne
        # peuvent, cumulés, qu'approcher le plafond -- cf. _BONUS_STUDIO +
        # _BONUS_SOURCE + _BONUS_DECADE = 0.07 < BONUS_CAP) : il ne peut venir
        # que d'un lien de franchise avéré (suite directe, ou -- pour un
        # personnage -- même origine). C'est une preuve directe de proximité,
        # pas un à-côté structurel, et le garder muet serait le même bug que
        # cette refonte corrige : deux personnages de la même œuvre qui ne
        # partagent ni trait ni organisation scoreraient zéro malgré le lien le
        # plus fort qui existe entre deux personnages.
        if base <= 0 and self.bonus < BONUS_CAP:
            return 0.0
        return min(1.0, base + self.bonus)


def _title(work: Dict[str, Any]) -> str:
    return work.get("title") or work.get("name") or ""


def vocabulary_of(work: Dict[str, Any]) -> set:
    """Le vocabulaire pondéré par IDF d'une œuvre OU d'un personnage.

    Tags et genres pour une œuvre (un genre n'est qu'un tag très fréquent, cf.
    build_index) ; traits et organisations (`entities.organizations`) pour un
    personnage -- le vrai catalogue personnages
    (data/processed/filtered_characters.json) n'a ni tags, ni genres, ni
    recommandations, seulement `origin`/`traits`/`entities`. Sans ce
    quatrième-et-cinquième vocabulaire fondu ici, ce signal est plat et le
    mode Personnages ne score jamais rien.
    """
    entities = work.get("entities") or {}
    return (
        set(work.get("tags") or [])
        | set(work.get("genres") or [])
        | set(work.get("traits") or [])
        | set(entities.get("organizations") or [])
    )


def build_index(works: List[Dict[str, Any]]) -> ProximityIndex:
    """Prépare une fois ce que les composantes reliront des milliers de fois."""
    by_title = {_title(w): w for w in works if _title(w)}

    reco: Dict[str, Dict[str, float]] = {}
    for title, work in by_title.items():
        vector = {}
        for other, votes in (work.get("recommendations") or {}).items():
            # AniList a des votes négatifs (des « non, rien à voir ») : on les ignore.
            if other in by_title and isinstance(votes, (int, float)) and votes > 0:
                vector[other] = math.log1p(votes)
        reco[title] = vector

    document_freq: Dict[str, int] = {}
    for work in by_title.values():
        # Un genre n'est qu'un tag très fréquent, et traits/organisations en sont
        # l'équivalent côté personnage : on fusionne tout dans le même vocabulaire
        # pondéré par IDF (cf. vocabulary_of). Sans ça, les jeux vidéo (0 tag, 100%
        # genres) et les personnages (ni tags ni genres, seulement traits/
        # organisations) n'ont aucun signal alors qu'un vrai en existe.
        vocabulary = vocabulary_of(work)
        for tag in vocabulary:
            document_freq[tag] = document_freq.get(tag, 0) + 1
    total = max(1, len(by_title))
    # Plancher à 0.0 : si un tag finissait par apparaître sur TOUTES les œuvres,
    # log(total / (1 + n)) deviendrait négatif et math.sqrt(weight_a * weight_b)
    # planterait (ValueError) dès qu'un poids agrégé devient négatif.
    idf = {tag: max(0.0, math.log(total / (1 + n))) for tag, n in document_freq.items()}

    return ProximityIndex(works=by_title, reco=reco, idf=idf)


def direct_reco(index: ProximityIndex, a: str, b: str) -> float:
    """« Les fans de A recommandent B » — l'arête la plus votée des deux sens."""
    votes = max(index.reco.get(a, {}).get(b, 0.0), index.reco.get(b, {}).get(a, 0.0))
    return min(1.0, votes / _MAX_VOTES)


def co_reco(index: ProximityIndex, a: str, b: str) -> float:
    """A et B sont recommandés aux MÊMES publics.

    C'est ce qui donne la densité : sans arête directe entre A et B, si les deux sont
    recommandées depuis Code Geass et Psycho-Pass, elles sont voisines.
    """
    va, vb = index.reco.get(a, {}), index.reco.get(b, {})
    shared = set(va) & set(vb)
    if not shared:
        return 0.0
    numerator = sum(va[k] * vb[k] for k in shared)
    norm_a = math.sqrt(sum(w * w for w in va.values()))
    norm_b = math.sqrt(sum(w * w for w in vb.values()))
    if not norm_a or not norm_b:
        return 0.0
    return numerator / (norm_a * norm_b)


def tag_overlap(index: ProximityIndex, a: str, b: str) -> float:
    """Vocabulaire partagé (tags, genres, traits, organisations), pondéré par sa rareté.

    Partager « Detective » vaut cher ; partager « Primarily Male Cast », que la moitié
    du catalogue porte, ne vaut presque rien -- et un genre n'est jamais qu'un tag très
    fréquent : « Action » sur la moitié du catalogue pèse à peine plus que ce tag-là.
    Même logique pour un personnage : partager une organisation rare (« Survey
    Corps ») vaut cher, un trait banal ne vaut presque rien (cf. vocabulary_of).
    """
    wa, wb = index.works.get(a, {}), index.works.get(b, {})
    ta = vocabulary_of(wa)
    tb = vocabulary_of(wb)
    shared = ta & tb
    if not shared:
        return 0.0
    numerator = sum(index.idf.get(t, 0.0) for t in shared)
    weight_a = sum(index.idf.get(t, 0.0) for t in ta)
    weight_b = sum(index.idf.get(t, 0.0) for t in tb)
    denominator = math.sqrt(weight_a * weight_b)
    return numerator / denominator if denominator else 0.0


def structural_bonus(index: ProximityIndex, a: str, b: str) -> float:
    """Même franchise, studio, source, décennie. Ne peut que compléter (cf. Components.total)."""
    wa, wb = index.works.get(a, {}), index.works.get(b, {})
    if not wa or not wb:
        return 0.0

    # Le vrai catalogue a des entrées auto-référentes (ex. "ADAPTATION": [son propre
    # titre]) : il faut les exclure, sinon deux œuvres sans aucun rapport, qui ont
    # chacune ce quirk, se retrouvent toutes les deux dans le même ensemble "related"
    # et se voient attribuer le bonus de franchise maximal à tort. La comparaison est
    # insensible à la casse : 55 entrées du vrai catalogue s'auto-référencent sous une
    # casse différente (ex. "VINLAND SAGA" listant ["Vinland Saga"]). Rien ne casse
    # aujourd'hui par coïncidence (aucune paire de titres du catalogue ne diffère
    # uniquement par la casse), mais l'exclusion doit tenir sans compter dessus.
    a_norm, b_norm = a.casefold(), b.casefold()
    a_related = {
        t
        for titles in (wa.get("relations") or {}).values()
        for t in titles
        if t.casefold() != a_norm
    }
    b_related = {
        t
        for titles in (wb.get("relations") or {}).values()
        for t in titles
        if t.casefold() != b_norm
    }
    if b in a_related or a in b_related:
        return BONUS_CAP  # une suite directe : rien de plus proche structurellement

    # Personnages : `origin` est l'œuvre d'origine. Deux personnages de la même
    # œuvre sont structurellement aussi proches qu'une suite directe l'est pour
    # deux œuvres -- ils héritent donc du même bonus plafond, pas d'un petit
    # incrément comme le studio partagé. Les œuvres n'ont pas de champ "origin" :
    # `wa.get("origin")` y est toujours None, donc ce test ne peut jamais
    # s'appliquer à une paire œuvre/œuvre par accident.
    if wa.get("origin") and wa.get("origin") == wb.get("origin"):
        return BONUS_CAP

    bonus = 0.0
    if set(wa.get("studios") or []) & set(wb.get("studios") or []):
        bonus += _BONUS_STUDIO
    if wa.get("source") and wa.get("source") == wb.get("source"):
        bonus += _BONUS_SOURCE
    ya, yb = wa.get("year"), wb.get("year")
    if ya and yb and int(ya) // 10 == int(yb) // 10:
        bonus += _BONUS_DECADE
    return min(BONUS_CAP, bonus)


def score(index: ProximityIndex, a: str, b: str) -> Components:
    return Components(
        direct=direct_reco(index, a, b),
        co_reco=co_reco(index, a, b),
        tags=tag_overlap(index, a, b),
        bonus=structural_bonus(index, a, b),
    )
