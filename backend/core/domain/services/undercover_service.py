import ast
import json
import logging
import os
import random
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Set

from .catalog_service import CatalogService
from .similarity_service import SimilarityService

logger = logging.getLogger("animetix.undercover")


# Top-N popularity ceiling for the cross-category universes (Mix / MixChar),
# which don't live in DIFFICULTY_SETTINGS. Easy = only the very famous works.
MIX_LIMITS = {"Easy": 150, "Normal": 400, "Hard": 1000, "Impossible": 2000}

# Every category the host can tick on/off individually. A pair may mix any of
# them (e.g. civil = anime, undercover = video game).
KNOWN_CATS = {"Anime", "Manga", "Character", "Movie", "Game", "Actor", "VGChar"}

# At least ONE word of every pair must come from an "anchor" category
# (anime/manga, or an anime/manga character). If the civil is already an anchor
# the other word can be strictly anything; only when the civil is off-anchor is
# the undercover forced back onto an anchor.
ANCHOR_CATS = {"Anime", "Manga", "Character"}

# These three carry a vector store → when a single one is selected we reuse the
# higher-quality semantic-neighbour pairing instead of the lexical one.
VECTOR_CATS = {"Anime", "Manga", "Character"}

# Where genre-ish tokens live per category — used to find "close but different"
# pairs across media. Characters/actors have no genre, so we fall back to gender.
GENRE_FIELDS = {
    "Anime": ["genres", "tags"],
    "Manga": ["genres", "tags"],
    "Movie": ["genres", "tags"],
    "Game": ["genres", "themes"],
}

# Free-text field carrying the synopsis/biography — its tokens feed the content
# proximity so e.g. an actor's bio can match an anime character's description.
DESC_FIELDS = {
    "Anime": "description",
    "Manga": "description",
    "Movie": "description",
    "Game": "description",
    "Character": "clean_description",
    "Actor": "biography",
}

# Genre/theme fields are categorical → kept as single canonical tokens (so
# "sci-fi" matches across media). Tags/description are free text → tokenised.
_GENRE_LIKE = {"genres", "themes"}

# Very common words stripped from name/description token sets to avoid spurious
# matches (FR + EN). Kept small on purpose.
_STOPWORDS = {
    "the",
    "a",
    "an",
    "of",
    "and",
    "to",
    "in",
    "is",
    "it",
    "as",
    "with",
    "for",
    "le",
    "la",
    "les",
    "un",
    "une",
    "des",
    "de",
    "du",
    "et",
    "est",
    "dans",
    "no",
    "wa",
    "ga",
    "ni",
    "season",
    "saison",
    "part",
    "movie",
    "film",
}

# Normalise FR (movies) and EN (anime/games) genre vocabularies onto a shared
# set so an anime and a film can actually be recognised as thematically close.
GENRE_ALIASES = {
    "aventure": "adventure",
    "comédie": "comedy",
    "comedie": "comedy",
    "drame": "drama",
    "horreur": "horror",
    "épouvante-horreur": "horror",
    "epouvante-horreur": "horror",
    "science-fiction": "sci-fi",
    "science fiction": "sci-fi",
    "sf": "sci-fi",
    "science-fiction & fantastique": "sci-fi",
    "fantastique": "fantasy",
    "fantaisie": "fantasy",
    "mystère": "mystery",
    "mystere": "mystery",
    "guerre": "war",
    "familial": "family",
    "famille": "family",
    "musique": "music",
    "musical": "music",
    "policier": "crime",
    "arts martiaux": "martial arts",
}


def _as_list(value) -> List:
    """Datasets store list fields either as real lists or as their str() repr."""
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        try:
            parsed = ast.literal_eval(s)
            return parsed if isinstance(parsed, list) else [parsed]
        except (ValueError, SyntaxError):
            return [s]
    return []


def _norm_genre(genre) -> str:
    g = str(genre).strip().lower()
    return GENRE_ALIASES.get(g, g)


def _fold(text) -> str:
    """Lower-case + strip accents so FR/EN tokens compare on equal footing."""
    norm = unicodedata.normalize("NFKD", str(text))
    return norm.encode("ascii", "ignore").decode("ascii").lower()


def _tokens(text) -> Set[str]:
    return {
        t
        for t in re.findall(r"[a-z0-9]+", _fold(text))
        if t not in _STOPWORDS and len(t) > 1
    }


def _jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    return inter / len(a | b) if inter else 0.0


def _overlap(a: Set[str], b: Set[str]) -> float:
    """Overlap coefficient — forgiving when the two token sets differ a lot in
    size (e.g. an actor's long bio vs an anime's short genre list)."""
    if not a or not b:
        return 0.0
    inter = len(a & b)
    return inter / min(len(a), len(b)) if inter else 0.0


def _proximity(a: Dict, b: Dict) -> float:
    """Cross-category semantic proximity = max of name proximity and content
    (genres/tags/description) proximity, as requested."""
    name_sim = max(
        SequenceMatcher(None, a["name_fold"], b["name_fold"]).ratio(),
        _jaccard(a["name_tokens"], b["name_tokens"]),
    )
    content_sim = _overlap(a["content_tokens"], b["content_tokens"])
    return max(name_sim, content_sim)


class UndercoverService:
    """
    Service gérant la logique spécifique du mode de jeu 'Undercover'.

    L'hôte coche librement les catégories à inclure (anime, manga, perso, film,
    jeu vidéo, acteur, perso de jeu vidéo). Deux régimes :
      - une seule catégorie « ancre » cochée → paire sémantiquement proche via le
        store vectoriel (comportement historique) ;
      - plusieurs catégories → paire croisée classée par proximité sémantique
        (max nom / contenu), avec la garantie qu'au moins un mot est une ancre.
    """

    def __init__(
        self, catalog_service: CatalogService, similarity_service: SimilarityService
    ):
        self.catalog_service = catalog_service
        self.similarity_service = similarity_service

    # ── Public API ──────────────────────────────────────────────────────────
    def start_game(
        self,
        categories: List[str],
        difficulty: str,
        player_ids: List[str],
        rank_limits: Dict,
        num_undercovers: int = 1,
    ) -> Dict:
        """Initialise une partie : choix des mots (civil + infiltré), rôles, images.

        `categories` est la liste des catégories cochées par l'hôte (anime,
        manga, perso, film, jeu, acteur, perso de jeu vidéo)."""
        cats = [c for c in (categories or []) if c in KNOWN_CATS]
        if not cats:
            cats = ["Anime"]
        anchors = {c for c in cats if c in ANCHOR_CATS}
        if not anchors:
            # Règle produit : un mot de la paire doit toujours être une ancre.
            return {}

        if len(cats) == 1 and cats[0] in VECTOR_CATS:
            # Une seule catégorie « ancre » → paire sémantique via le store vectoriel.
            pair = self._pick_single_pair(cats[0], difficulty, rank_limits)
        else:
            pair = self._pick_cross_pair(cats, anchors, difficulty)

        if not pair:
            return {}
        civil, undercover = pair

        # 3. Attribution des rôles — le nombre d'infiltrés est paramétrable, en
        # gardant au moins 2 civils pour que le jeu reste jouable.
        n = len(player_ids)
        k = max(1, min(int(num_undercovers or 1), max(1, n - 2)))
        undercover_ids = set(random.sample(player_ids, k)) if n else set()

        assignments = {}
        for p_id in player_ids:
            is_under = p_id in undercover_ids
            assignments[p_id] = {
                "role": "Undercover" if is_under else "Civil",
                "word": undercover["label"] if is_under else civil["label"],
                "image": undercover["image"] if is_under else civil["image"],
            }

        return {
            "civil_word": civil["label"],
            "undercover_word": undercover["label"],
            "assignments": assignments,
        }

    # ── Mono-catégorie (paire sémantiquement proche) ───────────────────────
    def _pick_single_pair(
        self, media_type: str, difficulty: str, rank_limits: Dict
    ) -> Optional[tuple]:
        catalog = self.catalog_service.get_catalog(media_type)
        if not catalog:
            return None

        limit = rank_limits.get(media_type, {}).get(difficulty, 300)
        valid = [
            t
            for t in catalog["lookup"][:limit]
            if (t.get("title") or t.get("name")) in catalog["title_to_full_data"]
        ]
        if not valid:
            return None

        civil_item = random.choice(valid)
        civil_label = civil_item.get("title") or civil_item.get("name")
        civil_data = catalog["title_to_full_data"][civil_label]
        civil_id = civil_data["id"]

        # Voisin proche (mais différent) via le store vectoriel.
        undercover_title = None
        try:
            similar = self.similarity_service.find_similar_items(
                media_type, str(civil_id), count=10
            )
            neighbors = (similar or {}).get("metadatas") or [[]]
            options = [
                (m.get("title") or m.get("name"))
                for m in neighbors[0]
                if str(m["id"]) != str(civil_id)
            ]
            if options:
                undercover_title = random.choice(options[:5])
        except Exception as e:
            logger.warning(f"Semantic word selection failed for Undercover: {e}")

        if not undercover_title:
            undercover_title = random.choice(
                [
                    (t.get("title") or t.get("name"))
                    for t in valid
                    if (t.get("title") or t.get("name")) != civil_label
                ]
            )

        under_data = catalog["title_to_full_data"].get(undercover_title, {})
        return (
            {"label": civil_label, "image": civil_data.get("image")},
            {"label": undercover_title, "image": under_data.get("image")},
        )

    # ── Univers croisés (Mix / MixChar) ────────────────────────────────────
    def _pick_cross_pair(
        self, categories: List[str], anchors: Set[str], difficulty: str
    ) -> Optional[tuple]:
        limit = MIX_LIMITS.get(difficulty, 400)
        pools: Dict[str, List[Dict]] = {}
        for cat in categories:
            try:
                pool = self._load_pool(cat, limit)
                if pool:
                    pools[cat] = pool
            except Exception as e:
                logger.warning(f"Undercover pool '{cat}' unavailable: {e}")

        if not pools:
            return None

        cats = list(pools.keys())
        anchor_cats = [c for c in cats if c in anchors]
        if not anchor_cats:
            return None  # impossible de garantir un mot anime/manga/perso

        # Le mot CIVIL (celui que la majorité voit) est TOUJOURS une ancre
        # anime/manga/perso : on garantit ainsi qu'un anime/manga est présent et
        # bien visible, jamais noyé côté infiltré.
        civil_cat = random.choice(anchor_cats)
        civil = random.choice(pools[civil_cat])

        # L'infiltré prend de préférence une catégorie NON-ancre (film, jeu,
        # acteur, perso de jeu) → vraie paire croisée. S'il n'y en a aucune de
        # cochée, on retombe sur une ancre (manche anime/manga classique).
        non_anchor_cats = [c for c in cats if c not in anchors]
        under_cats = non_anchor_cats or anchor_cats
        candidates = [
            e for c in under_cats for e in pools[c] if e["label"] != civil["label"]
        ]
        if not candidates:
            candidates = [
                e for c in anchor_cats for e in pools[c] if e["label"] != civil["label"]
            ]
        if not candidates:
            return None

        # On classe par proximité sémantique (max nom / contenu) puis on tire au
        # sort dans le haut du classement, pondéré par le score : les paires
        # restent proches mais ne sont jamais figées.
        scored = sorted(
            ((_proximity(civil, e), e) for e in candidates),
            key=lambda x: x[0],
            reverse=True,
        )
        top = scored[: max(6, len(scored) // 15)]
        weights = [score**2 + 0.01 for score, _ in top]
        undercover = random.choices([e for _, e in top], weights=weights, k=1)[0]
        return civil, undercover

    def _load_pool(self, category: str, limit: int) -> List[Dict]:
        """Construit un pool normalisé (label, image, tokens) pour une catégorie."""
        if category == "VGChar":
            raw = self._load_vg_chars()[:limit]
            entries = [self._make_entry(it, category) for it in raw]
            return [e for e in entries if e]

        catalog = self.catalog_service.get_catalog(category)
        lookup = (catalog or {}).get("lookup") or []
        t2d = (catalog or {}).get("title_to_full_data") or {}
        entries = []
        for row in lookup[:limit]:
            label = row.get("title") or row.get("name")
            item = t2d.get(str(label))
            if item:
                entry = self._make_entry(item, category)
                if entry:
                    entries.append(entry)
        return entries

    def _make_entry(self, item: Dict, category: str) -> Optional[Dict]:
        label = item.get("title") or item.get("name")
        if not label:
            return None
        name = str(label)

        # Content tokens: canonical genre/theme tokens + free-text tag/synopsis
        # tokens. These drive the genres/tags/description proximity.
        content: Set[str] = set()
        for field in GENRE_FIELDS.get(category, []):
            for g in _as_list(item.get(field))[:10]:
                if field in _GENRE_LIKE:
                    canon = _fold(_norm_genre(g)).replace(" ", "").replace("-", "")
                    if canon:
                        content.add(f"gn_{canon}")
                else:  # tags = free text
                    content |= _tokens(g)
        gender = item.get("gender")
        if gender:
            content.add(f"g_{_fold(gender).strip()}")
        desc_field = DESC_FIELDS.get(category)
        if desc_field:
            # Cap synopsis tokens so a long bio can't dwarf the rest.
            content |= set(list(_tokens(item.get(desc_field) or ""))[:60])

        return {
            "label": name,
            "image": item.get("image"),
            "name_fold": _fold(name),
            "name_tokens": _tokens(name),
            "content_tokens": content,
        }

    def _load_vg_chars(self) -> List[Dict]:
        root = getattr(self.catalog_service.repository, "project_root", "") or getattr(
            self.catalog_service.sql_repository, "project_root", ""
        )
        path = os.path.join(root, "data", "artifacts", "vg_char_data_for_lookup.json")
        with open(path, encoding="utf-8") as f:
            return json.load(f)
