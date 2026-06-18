# -*- coding: utf-8 -*-
"""
Compilateur de jeu de données de préférence DPO / RLHF.
Génère offline des paires (chosen, rejected) à partir du jeu de données SFT.
"""

import json  # noqa: E402
import logging  # noqa: E402
import os  # noqa: E402
import random  # noqa: E402
import re  # noqa: E402
import sys  # noqa: E402
from typing import List  # noqa: E402

# Insert paths at 0 to avoid name conflicts with virtualenv packages
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
api_path = os.path.join(backend_path, "api")
if api_path not in sys.path:
    sys.path.insert(0, api_path)

logger = logging.getLogger("animetix.pipeline.mlops.dpo_dataset_compiler")
logging.basicConfig(level=logging.INFO)

import hashlib  # noqa: E402

from pydantic import BaseModel, field_validator, model_validator  # noqa: E402

# Cache variables
DPO_CACHE_FILE = None
DPO_CACHE = {}

# --- Regex patterns for sample validation ---
_HTML_TAG_RE = re.compile(r"<[a-zA-Z][^>]*>")
_UNCLOSED_CODE_BLOCK_RE = re.compile(r"```")
_API_ERROR_PATTERNS = [
    re.compile(r"(?i)^\s*error\s*:", re.MULTILINE),
    re.compile(r"(?i)\b\d{3}\s+internal\s+server\s+error\b"),
    re.compile(r'^\s*\{\s*"error"', re.MULTILINE),
    re.compile(r"(?i)<!DOCTYPE\s+html>", re.MULTILINE),
]


class DPOSampleValidator(BaseModel):
    """
    Schéma Pydantic pour valider chaque échantillon DPO compilé.
    Élimine les résidus HTML, les balises de code mal formées,
    les réponses d'API en échec, et les champs vides.
    """

    prompt: str
    chosen: str
    rejected: str

    @field_validator("prompt", "chosen", "rejected")
    @classmethod
    def must_not_be_blank(cls, v: str, info) -> str:
        if not v or not v.strip():
            raise ValueError(
                f"Le champ '{info.field_name}' ne doit pas être vide ou composé uniquement d'espaces."
            )
        return v

    @field_validator("chosen", "rejected")
    @classmethod
    def must_not_contain_html(cls, v: str, info) -> str:
        if _HTML_TAG_RE.search(v):
            raise ValueError(
                f"Le champ '{info.field_name}' contient des résidus HTML : {_HTML_TAG_RE.findall(v)[:3]}"
            )
        return v

    @field_validator("chosen", "rejected")
    @classmethod
    def must_not_have_unclosed_code_blocks(cls, v: str, info) -> str:
        count = len(_UNCLOSED_CODE_BLOCK_RE.findall(v))
        if count % 2 != 0:
            raise ValueError(
                f"Le champ '{info.field_name}' contient un bloc de code non fermé (``` impair)."
            )
        return v

    @field_validator("chosen", "rejected")
    @classmethod
    def must_not_be_api_error(cls, v: str, info) -> str:
        for pattern in _API_ERROR_PATTERNS:
            if pattern.search(v):
                raise ValueError(
                    f"Le champ '{info.field_name}' ressemble à une réponse d'API en échec."
                )
        return v

    @model_validator(mode="after")
    def chosen_must_differ_from_rejected(self):
        if self.chosen.strip() == self.rejected.strip():
            raise ValueError(
                "Les champs 'chosen' et 'rejected' sont identiques — la paire DPO est invalide."
            )
        return self


def init_dpo_cache(data_dir: str):
    global DPO_CACHE_FILE, DPO_CACHE
    DPO_CACHE_FILE = os.path.join(data_dir, "gemini_dpo_cache.json")
    if os.path.exists(DPO_CACHE_FILE):
        try:
            with open(DPO_CACHE_FILE, "r", encoding="utf-8") as f:
                DPO_CACHE = json.load(f)
            logger.info(f"Loaded {len(DPO_CACHE)} entries from DPO cache.")
        except Exception as e:
            logger.warning(f"Failed to load DPO cache: {e}")
            DPO_CACHE = {}
    else:
        DPO_CACHE = {}


def save_dpo_cache():
    if DPO_CACHE_FILE:
        try:
            os.makedirs(os.path.dirname(DPO_CACHE_FILE), exist_ok=True)
            with open(DPO_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(DPO_CACHE, f, ensure_ascii=False, indent=2)
            logger.info("Saved DPO cache to disk.")
        except Exception as e:
            logger.warning(f"Failed to save DPO cache: {e}")


try:
    from google import genai  # noqa: E402
except ImportError:
    genai = None

GEMINI_CLIENT = None
GEMINI_MODEL = "gemini-2.5-flash"


def init_gemini_client():
    global GEMINI_CLIENT, GEMINI_MODEL
    from dotenv import load_dotenv  # noqa: E402

    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    load_dotenv(os.path.join(base_dir, ".env"))
    api_key = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("ANIMETIX_GEMINI_MODEL", "gemini-2.5-flash")
    if api_key and genai is not None:
        try:
            GEMINI_CLIENT = genai.Client(api_key=api_key)
            logger.info("Gemini API client initialized for LLM-as-a-Judge.")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini API client: {e}")
            GEMINI_CLIENT = None
    else:
        logger.warning(
            "Gemini client not initialized (missing API key or google-genai dependency)."
        )
        GEMINI_CLIENT = None


# Tentatives d'importation des bases locales d'entités pour la substitution factuelle
try:
    from creators_db import CREATORS_AND_STUDIOS  # noqa: E402
except ImportError:
    try:
        from backend.pipeline.mlops.creators_db import (  # noqa: E402
            CREATORS_AND_STUDIOS,
        )
    except ImportError:
        CREATORS_AND_STUDIOS = {}

try:
    from french_market_db import FRENCH_ANIME_DISTRIBUTORS  # noqa: E402
    from french_market_db import FRENCH_MANGA_PUBLISHERS, FRENCH_VOICE_ACTORS
except ImportError:
    try:
        from backend.pipeline.mlops.french_market_db import (  # noqa: E402
            FRENCH_ANIME_DISTRIBUTORS,
            FRENCH_MANGA_PUBLISHERS,
            FRENCH_VOICE_ACTORS,
        )
    except ImportError:
        FRENCH_VOICE_ACTORS = {}
        FRENCH_MANGA_PUBLISHERS = {}
        FRENCH_ANIME_DISTRIBUTORS = {}

try:
    from japanese_market_db import JAPANESE_ANIME_DISTRIBUTORS  # noqa: E402
    from japanese_market_db import JAPANESE_MANGA_PUBLISHERS
except ImportError:
    try:
        from backend.pipeline.mlops.japanese_market_db import (  # noqa: E402
            JAPANESE_ANIME_DISTRIBUTORS,
            JAPANESE_MANGA_PUBLISHERS,
        )
    except ImportError:
        JAPANESE_MANGA_PUBLISHERS = {}
        JAPANESE_ANIME_DISTRIBUTORS = {}

# Listes d'entités par défaut en cas d'échec d'importation
STUDIOS_LIST = (
    list(CREATORS_AND_STUDIOS.keys())
    if CREATORS_AND_STUDIOS
    else [
        "Wit Studio",
        "Studio Ghibli",
        "MAPPA",
        "ufotable",
        "Madhouse",
        "Shaft",
        "Studio Trigger",
        "Bones",
        "Sunrise",
        "Toei Animation",
    ]
)

VOICE_ACTORS_LIST = (
    list(FRENCH_VOICE_ACTORS.keys())
    if FRENCH_VOICE_ACTORS
    else [
        "Brigitte Lecordier",
        "Benoît DuPac",
        "Alexis Tomassian",
        "Arthur Pestel",
        "Patrick Borg",
        "Eric Legrand",
        "Philippe Ariotti",
    ]
)

PUBLISHERS_LIST = (
    list(FRENCH_MANGA_PUBLISHERS.keys())
    if FRENCH_MANGA_PUBLISHERS
    else [
        "Glénat Manga",
        "Kana",
        "Pika Édition",
        "Kurokawa",
        "Ki-oon",
        "Delcourt/Tonkam",
        "Soleil Manga",
        "Akata",
        "Meian",
    ]
) + (
    list(JAPANESE_MANGA_PUBLISHERS.keys())
    if JAPANESE_MANGA_PUBLISHERS
    else [
        "Shūeisha",
        "Kōdansha",
        "Shōgakukan",
        "Kadokawa Future Publishing",
        "Square Enix Manga",
    ]
)

DISTRIBUTORS_LIST = (
    list(FRENCH_ANIME_DISTRIBUTORS.keys())
    if FRENCH_ANIME_DISTRIBUTORS
    else [
        "Crunchyroll France",
        "ADN",
        "Netflix France",
        "Prime Video Channels",
        "Disney+ France",
        "Wakanim",
    ]
) + (
    list(JAPANESE_ANIME_DISTRIBUTORS.keys())
    if JAPANESE_ANIME_DISTRIBUTORS
    else [
        "Aniplex",
        "Tōhō",
        "Toei Animation",
        "Bandai Namco Filmworks",
        "Pony Canyon",
        "TV Tokyo",
    ]
)

JAPANESE_PUBLISHERS_SET = (
    set(JAPANESE_MANGA_PUBLISHERS.keys())
    if JAPANESE_MANGA_PUBLISHERS
    else {
        "Shūeisha",
        "Kōdansha",
        "Shōgakukan",
        "Kadokawa Future Publishing",
        "Square Enix Manga",
    }
)

JAPANESE_DISTRIBUTORS_SET = (
    set(JAPANESE_ANIME_DISTRIBUTORS.keys())
    if JAPANESE_ANIME_DISTRIBUTORS
    else {
        "Aniplex",
        "Tōhō",
        "Toei Animation",
        "Bandai Namco Filmworks",
        "Pony Canyon",
        "TV Tokyo",
    }
)

POPULAR_TITLES = [
    "One Piece",
    "Naruto",
    "Bleach",
    "Death Note",
    "Berserk",
    "Dragon Ball Z",
    "My Hero Academia",
    "Jujutsu Kaisen",
    "L'Attaque des Titans",
    "Attack on Titan",
    "Neon Genesis Evangelion",
    "Demon Slayer",
    "GTO",
    "Fullmetal Alchemist",
    "Sword Art Online",
    "Chainsaw Man",
    "Spy x Family",
    "Hunter x Hunter",
    "Tokyo Ghoul",
    "Fairy Tail",
]


# --- PRECOMPUTATION OF CLOSE-CONCEPTS RELATION MAPPINGS ---
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
ANIME_DB = os.path.join(BASE_DIR, "data", "processed", "clean_root_animes.json")
MANGA_DB = os.path.join(BASE_DIR, "data", "processed", "clean_root_mangas.json")

MANGAKAS_LIST = []
DIRECTORS_LIST = []
STUDIOS_ONLY_LIST = []

if CREATORS_AND_STUDIOS:
    keys = list(CREATORS_AND_STUDIOS.keys())
    MANGAKAS_LIST = keys[:48]
    DIRECTORS_LIST = keys[48:68]
    STUDIOS_ONLY_LIST = keys[68:]
else:
    STUDIOS_ONLY_LIST = STUDIOS_LIST

title_genres = {}
studio_genres = {}

if os.path.exists(ANIME_DB):
    try:
        with open(ANIME_DB, "r", encoding="utf-8") as f:
            animes = json.load(f)
            for a in animes:
                genres = set(g.lower() for g in a.get("genres", []) + a.get("tags", []))
                for key_title in [
                    a.get("title"),
                    a.get("title_english"),
                    a.get("title_native"),
                ]:
                    if key_title:
                        title_genres[key_title.strip().lower()] = genres
                for s in a.get("studios", []):
                    s_clean = s.strip()
                    if s_clean:
                        if s_clean not in studio_genres:
                            studio_genres[s_clean] = set()
                        studio_genres[s_clean].update(genres)
    except Exception as e:
        logger.warning(f"Failed to load anime DB in DPO compiler: {e}")

if os.path.exists(MANGA_DB):
    try:
        with open(MANGA_DB, "r", encoding="utf-8") as f:
            mangas = json.load(f)
            for m in mangas:
                genres = set(g.lower() for g in m.get("genres", []) + m.get("tags", []))
                for key_title in [
                    m.get("title"),
                    m.get("title_english"),
                    m.get("title_native"),
                ]:
                    if key_title:
                        title_genres[key_title.strip().lower()] = genres
    except Exception as e:
        logger.warning(f"Failed to load manga DB in DPO compiler: {e}")

RELATED_ENTITIES_MAP = {}

# 1. Voice Actors
va_series = {}
if FRENCH_VOICE_ACTORS:
    for va_name, va_data in FRENCH_VOICE_ACTORS.items():
        examples = va_data.get("examples", "")
        titles = re.findall(r"\*(.*?)\*", examples)
        clean_titles = {t.lower().strip() for t in titles if t}
        va_series[va_name] = clean_titles

for va_name in VOICE_ACTORS_LIST:
    va_titles = va_series.get(va_name, set())
    similarities = []
    for other_va in VOICE_ACTORS_LIST:
        if other_va.lower() == va_name.lower():
            continue
        other_titles = va_series.get(other_va, set())
        overlap = len(va_titles.intersection(other_titles))
        similarities.append((other_va, overlap))
    similarities.sort(key=lambda x: x[1], reverse=True)
    candidates = [va for va, overlap in similarities if overlap > 0]
    if candidates:
        RELATED_ENTITIES_MAP[va_name] = candidates[:3]
    else:
        RELATED_ENTITIES_MAP[va_name] = [
            va for va in VOICE_ACTORS_LIST if va.lower() != va_name.lower()
        ]

# 2. Studios
for studio_name in STUDIOS_ONLY_LIST:
    s_genres = studio_genres.get(studio_name, set())
    similarities = []
    for other_s in STUDIOS_ONLY_LIST:
        if other_s.lower() == studio_name.lower():
            continue
        other_genres = studio_genres.get(other_s, set())
        intersection = s_genres.intersection(other_genres)
        union = s_genres.union(other_genres)
        jaccard = len(intersection) / len(union) if union else 0.0
        similarities.append((other_s, jaccard))
    similarities.sort(key=lambda x: x[1], reverse=True)
    candidates = [s for s, sim in similarities if sim > 0]
    if candidates:
        RELATED_ENTITIES_MAP[studio_name] = candidates[:3]
    else:
        RELATED_ENTITIES_MAP[studio_name] = [
            s for s in STUDIOS_ONLY_LIST if s.lower() != studio_name.lower()
        ]

# 3. Mangakas and Directors (from CREATORS_AND_STUDIOS)
creator_genres = {}
if CREATORS_AND_STUDIOS:
    for name, info in CREATORS_AND_STUDIOS.items():
        examples = info.get("examples", "")
        titles = re.findall(r"\*(.*?)\*", examples)
        clean_titles = [t.lower().strip() for t in titles if t]
        genres_tags = set()
        for t in clean_titles:
            if t in title_genres:
                genres_tags.update(title_genres[t])
        creator_genres[name] = genres_tags

# Map Mangakas
for name in MANGAKAS_LIST:
    m_genres = creator_genres.get(name, set())
    similarities = []
    for other_name in MANGAKAS_LIST:
        if other_name.lower() == name.lower():
            continue
        other_genres = creator_genres.get(other_name, set())
        intersection = m_genres.intersection(other_genres)
        union = m_genres.union(other_genres)
        jaccard = len(intersection) / len(union) if union else 0.0
        similarities.append((other_name, jaccard))
    similarities.sort(key=lambda x: x[1], reverse=True)
    candidates = [n for n, sim in similarities if sim > 0]
    if candidates:
        RELATED_ENTITIES_MAP[name] = candidates[:3]
    else:
        RELATED_ENTITIES_MAP[name] = [
            n for n in MANGAKAS_LIST if n.lower() != name.lower()
        ]

# Map Directors
for name in DIRECTORS_LIST:
    d_genres = creator_genres.get(name, set())
    similarities = []
    for other_name in DIRECTORS_LIST:
        if other_name.lower() == name.lower():
            continue
        other_genres = creator_genres.get(other_name, set())
        intersection = d_genres.intersection(other_genres)
        union = d_genres.union(other_genres)
        jaccard = len(intersection) / len(union) if union else 0.0
        similarities.append((other_name, jaccard))
    similarities.sort(key=lambda x: x[1], reverse=True)
    candidates = [n for n, sim in similarities if sim > 0]
    if candidates:
        RELATED_ENTITIES_MAP[name] = candidates[:3]
    else:
        RELATED_ENTITIES_MAP[name] = [
            n for n in DIRECTORS_LIST if n.lower() != name.lower()
        ]

# 4. Manga Publishers
PUBLISHER_GROUPS = {
    "Glénat Manga": "shonen_giant",
    "Kana": "shonen_giant",
    "Pika Édition": "shonen_giant",
    "Kurokawa": "shonen_giant",
    "Ki-oon": "shonen_giant",
    "Crunchyroll Manga": "shonen_giant",
    "Delcourt/Tonkam": "seinen_classic",
    "Vega-Dupuis": "seinen_classic",
    "Meian": "seinen_classic",
    "Ototo": "isekai_light_novel",
    "Mana Books": "video_games",
    "Soleil Manga": "video_games",
    "Akata": "indie_societal",
    "ChattoChatto": "indie_societal",
    "Taifu Comics": "yaoi_yuri",
    # Japanese publishers
    "Shūeisha": "jp_major",
    "Kōdansha": "jp_major",
    "Shōgakukan": "jp_major",
    "Kadokawa Future Publishing": "jp_conglom",
    "Media Factory": "jp_conglom",
    "Square Enix Manga": "jp_gangan",
    "Mag Garden": "jp_gangan",
    "Hakusensha": "jp_seinen_shojo",
    "Shodensha": "jp_seinen_shojo",
    "Akita Shoten": "jp_action_furyo",
    "Futabasha": "jp_action_furyo",
    "Houbunsha": "jp_kirara",
    "Ichijinsha": "jp_otaku",
    "Tokuma Shoten": "jp_historic",
    "Leed Publishing": "jp_historic",
}
for pub_name in PUBLISHERS_LIST:
    grp = PUBLISHER_GROUPS.get(pub_name)
    is_jp = pub_name in JAPANESE_PUBLISHERS_SET
    regional_candidates = [
        p for p in PUBLISHERS_LIST if (p in JAPANESE_PUBLISHERS_SET) == is_jp
    ]

    if grp:
        same_group = [
            p
            for p in regional_candidates
            if PUBLISHER_GROUPS.get(p) == grp and p.lower() != pub_name.lower()
        ]
        if same_group:
            RELATED_ENTITIES_MAP[pub_name] = same_group
            continue
    RELATED_ENTITIES_MAP[pub_name] = [
        p for p in regional_candidates if p.lower() != pub_name.lower()
    ]

# 5. Distributors
DISTRIBUTOR_GROUPS = {
    "Crunchyroll France": "streaming_specialist",
    "ADN": "streaming_specialist",
    "Wakanim": "streaming_specialist",
    "Netflix France": "streaming_generalist",
    "Disney+ France": "streaming_generalist",
    "Prime Video Channels": "streaming_generalist",
    "Club Dorothée": "retro_broadcaster",
    "Kazé": "physical_distributor",
    "Dybex": "physical_distributor",
    "Declic Images": "physical_distributor",
    # Japanese distributors
    "Aniplex": "jp_producer",
    "Kadokawa Anime": "jp_producer",
    "Pony Canyon": "jp_producer",
    "Tōhō": "jp_film_distributor",
    "Toei Animation": "jp_film_distributor",
    "Bandai Namco Filmworks": "jp_sci_fi",
    "TV Tokyo": "jp_tv",
    "Fuji TV": "jp_tv",
    "MBS TV": "jp_tv",
    "NHK": "jp_public_tv",
}
for dist_name in DISTRIBUTORS_LIST:
    grp = DISTRIBUTOR_GROUPS.get(dist_name)
    is_jp = dist_name in JAPANESE_DISTRIBUTORS_SET
    regional_candidates = [
        d for d in DISTRIBUTORS_LIST if (d in JAPANESE_DISTRIBUTORS_SET) == is_jp
    ]

    if grp:
        same_group = [
            d
            for d in regional_candidates
            if DISTRIBUTOR_GROUPS.get(d) == grp and d.lower() != dist_name.lower()
        ]
        if same_group:
            RELATED_ENTITIES_MAP[dist_name] = same_group
            continue
        if grp == "retro_broadcaster":
            phys = [
                d
                for d in regional_candidates
                if DISTRIBUTOR_GROUPS.get(d) == "physical_distributor"
            ]
            if phys:
                RELATED_ENTITIES_MAP[dist_name] = phys
                continue
    RELATED_ENTITIES_MAP[dist_name] = [
        d for d in regional_candidates if d.lower() != dist_name.lower()
    ]

# 6. Popular Titles
for title_name in POPULAR_TITLES:
    t_genres = title_genres.get(title_name.lower(), set())
    similarities = []
    for other_t in POPULAR_TITLES:
        if other_t.lower() == title_name.lower():
            continue
        other_genres = title_genres.get(other_t.lower(), set())
        intersection = t_genres.intersection(other_genres)
        union = t_genres.union(other_genres)
        jaccard = len(intersection) / len(union) if union else 0.0
        similarities.append((other_t, jaccard))
    similarities.sort(key=lambda x: x[1], reverse=True)
    candidates = [t for t, sim in similarities if sim > 0]
    if candidates:
        RELATED_ENTITIES_MAP[title_name] = candidates[:3]
    else:
        RELATED_ENTITIES_MAP[title_name] = [
            t for t in POPULAR_TITLES if t.lower() != title_name.lower()
        ]


def corrupt_fact_substitution(text: str, language: str = "Français") -> str:
    """
    Substitue des entités (studios, doubleurs, éditeurs, titres, années) par d'autres valeurs incorrectes.
    Garantit toujours qu'une modification a lieu (avec repli sur les chiffres ou les mots).
    """
    original_text = text
    modified = False

    # 1. Remplacer les années (ex: 2018 -> 1995)
    years = re.findall(r"\b(19\d\d|20\d\d)\b", text)
    if years:
        for yr in set(years):
            new_yr = str(random.choice([y for y in range(1980, 2027) if str(y) != yr]))
            text = re.sub(rf"\b{yr}\b", new_yr, text)
            modified = True

    # Helper pour remplacer les entités d'une liste
    def replace_from_list(current_text: str, entities: List[str]) -> tuple[str, bool]:
        text_mod = current_text
        found_any = False
        sorted_entities = sorted(entities, key=len, reverse=True)
        for ent in sorted_entities:
            pattern = rf"\b{re.escape(ent)}\b"
            if re.search(pattern, text_mod, re.IGNORECASE):
                # Look up closely related entities first
                choices = RELATED_ENTITIES_MAP.get(ent)
                if not choices:
                    choices = [e for e in entities if e.lower() != ent.lower()]
                if choices:
                    rep = random.choice(choices)
                    text_mod = re.sub(
                        pattern, lambda m: rep, text_mod, flags=re.IGNORECASE
                    )
                    found_any = True
                    break
        return text_mod, found_any

    # Appliquer les substitutions d'entités
    for entity_list in [
        STUDIOS_LIST,
        VOICE_ACTORS_LIST,
        PUBLISHERS_LIST,
        DISTRIBUTORS_LIST,
        POPULAR_TITLES,
    ]:
        text, is_mod = replace_from_list(text, entity_list)
        if is_mod:
            modified = True

    # 2. Si aucune modification n'a eu lieu, corrompre n'importe quel nombre
    if not modified:
        numbers = re.findall(r"\b\d+\b", text)
        if numbers:
            for num in set(numbers):
                new_num = str(
                    random.choice([n for n in range(1, 101) if str(n) != num])
                )
                text = re.sub(rf"\b{num}\b", new_num, text)
                modified = True

    # 3. Repli ultime : inverser deux mots de longueur >= 4
    if not modified or text == original_text:
        words = text.split()
        eligible_indices = [i for i, w in enumerate(words) if len(w) >= 4]
        if len(eligible_indices) >= 2:
            idx1, idx2 = random.sample(eligible_indices, 2)
            words[idx1], words[idx2] = words[idx2], words[idx1]
            text = " ".join(words)

    return text


def corrupt_tonal_deviation(text: str, language: str = "Français") -> str:
    """
    Dégrade le ton en choisissant aléatoirement l'un des trois types de corruption :
    1. Code-switching excessif (mélange fr/en ou en/jp non naturel)
    2. Redondance excessive (répétitions de propositions ou de phrases)
    3. Ton condescendant (ajouts de formules hautaines et pédantes)
    """
    strategy = random.choice(["code_switching", "redundancy", "condescending"])

    if strategy == "code_switching":
        if language == "Français":
            swaps = {
                r"\bpersonnages?\b": lambda m: (
                    "characters" if m.group(0).endswith("s") else "character"
                ),
                r"\bréalisateurs?\b": lambda m: (
                    "directors" if m.group(0).endswith("s") else "director"
                ),
                r"\bdirecteurs?\b": lambda m: (
                    "directors" if m.group(0).endswith("s") else "director"
                ),
                r"\bhistoire\b": "plotline",
                r"\bscénario\b": "storyline",
                r"\bchef-d'œuvre\b": "masterpiece",
                r"\bchefs-d'œuvre\b": "masterpieces",
                r"\bépisodes?\b": lambda m: (
                    "episodes" if m.group(0).endswith("s") else "episode"
                ),
                r"\bséries?\b": lambda m: (
                    "shows" if m.group(0).endswith("s") else "show"
                ),
                r"\banimation\b": "art style",
                r"\bdessins?\b": "art style",
                r"\bdiffusés?\b": "released",
                r"\bsortis?\b": "released",
                r"\béditeurs?\b": "publisher",
                r"\bédités?\b": "published",
            }
            for pattern, replacement in swaps.items():
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

            prependers = ["Basically, ", "Honestly, ", "Anyway, "]
            appenders = [
                ", which is totally fine.",
                ", literally.",
                ", fr fr.",
                ", actually.",
            ]
            text = random.choice(prependers) + text[0].lower() + text[1:]
            text = text.rstrip(".") + random.choice(appenders)
        else:
            swaps_en = {
                r"\bcharacters?\b": "chara",
                r"\bmasterpiece\b": "kami-sama tier masterpiece",
                r"\bfriends?\b": "nakama",
                r"\bprotagonists?\b": "MC",
                r"\bheros?\b": "MC",
                r"\banimation\b": "sakuga",
            }
            for pattern, replacement in swaps_en.items():
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

            prependers = ["So, basically, ", "Like, honestly, "]
            appenders = [", which is fine.", ", literally.", ", fr fr."]
            text = random.choice(prependers) + text[0].lower() + text[1:]
            text = text.rstrip(".") + random.choice(appenders)

    elif strategy == "redundancy":
        prependers = [
            "Pour ce qui est de ce sujet, et afin de préciser les choses de manière très précise, "
        ]
        appenders = [
            ", et comme je l'ai déjà expliqué et mentionné précédemment dans mon explication à ce sujet, c'est tout à fait cela.",
            ", ce qui signifie et veut dire exactement ce que cela signifie.",
        ]
        sentences = re.split(r"(?<=[.!?])\s+", text)
        if len(sentences) > 1:
            idx = random.randint(0, len(sentences) - 1)
            target = sentences[idx].rstrip(".!? ")
            if target:
                dup = f"Je répète donc que {target[0].lower() + target[1:]}."
                sentences.insert(idx + 1, dup)
            text = " ".join(sentences)
        else:
            text = random.choice(prependers) + text[0].lower() + text[1:]
            text = text.rstrip(".") + random.choice(appenders)

    elif strategy == "condescending":
        prependers = [
            "C'est pourtant évident, et tout otaku digne de ce nom devrait le savoir : ",
            "Franchement, il est élémentaire de comprendre que : ",
            "Pour peu que l'on s'y connaisse un minimum en japanimation, on sait bien que : ",
            "C'est une question triviale... Tout le monde sait que : ",
        ]
        appenders = [
            " Mais bon, il faut avoir un minimum de culture pour s'en rendre compte.",
            " C'est pourtant la base.",
            " (Enfin, si tant est que tu puisses comprendre cela).",
        ]
        inlines = [
            ", comme n'importe quel amateur de base l'aurait compris,",
            ", ce qui va de soi pour n'importe qui de cultivé,",
            ", bien que les néophytes en doutent,",
        ]
        if "," in text:
            parts = text.split(",", 1)
            text = parts[0] + random.choice(inlines) + parts[1]
        else:
            words = text.split()
            if len(words) > 4:
                words.insert(4, random.choice(inlines).strip())
                text = " ".join(words)

        text = random.choice(prependers) + text[0].lower() + text[1:]
        text = text.rstrip(".") + random.choice(appenders)

    return text.strip()


def corrupt_abrupt_truncation(text: str) -> str:
    """
    Simule une coupure brutale de génération en coupant au milieu du texte.
    """
    if len(text) < 10:
        return text

    ratio = random.uniform(0.3, 0.7)
    cut_idx = int(len(text) * ratio)
    truncated = text[:cut_idx].rstrip()

    # Nettoyer les ponctuations de fin pour que la coupure soit vraiment abrupte
    truncated = re.sub(r"[.,!?;:\s]+$", "", truncated)
    return truncated


def corrupt_evasive_refusal(text: str, language: str = "Français") -> str:
    """
    Remplace toute la réponse par un refus évasif non-informatif.
    """
    fr_refusals = [
        "Désolé, je ne dispose pas de ces informations pour le moment.",
        "Aucune idée, je ne connais pas ce sujet.",
        "Désolé, je n'ai pas le temps de répondre à ça, cherche sur Google.",
    ]
    en_refusals = [
        "Sorry, I don't have this information.",
        "Sorry, I have no idea about this.",
        "I don't know, search on Google.",
    ]

    refusals = en_refusals if language == "English" else fr_refusals
    return random.choice(refusals)


def corrupt_llm_critic(chosen: str, language: str = "Français") -> str:
    """
    Critiques et corrompt la réponse chosen via Gemini pour y introduire une erreur logique/factuelle.
    Utilise le cache local et retombe sur la substitution factuelle heuristique en cas de panne.
    """
    import time  # noqa: E402

    chosen_hash = hashlib.md5(chosen.encode("utf-8"), usedforsecurity=False).hexdigest()
    if chosen_hash in DPO_CACHE:
        return DPO_CACHE[chosen_hash]

    if not GEMINI_CLIENT:
        return corrupt_fact_substitution(chosen, language)

    prompt = (
        "Tu es un critique expert et rigoureux de la japanimation, des mangas, et de la culture otaku.\n"
        "Prends la réponse correcte suivante et réécris-la pour y introduire une et une seule erreur logique, chronologique ou factuelle subtile (ex: inverser deux personnages proches, confondre deux studios ayant produit des œuvres du même genre, ou intervertir une année de sortie).\n"
        "La réponse modifiée doit conserver exactement le même ton d'expert, le même niveau de détail et être rédigée de manière fluide en français. Elle doit sembler parfaitement plausible à un lecteur non averti.\n\n"
        "Réponse correcte :\n"
        f"{chosen}\n\n"
        "Renvoie uniquement la réponse modifiée, sans aucune introduction, salutation ou explication."
    )

    for attempt in range(3):
        try:
            response = GEMINI_CLIENT.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            if response.text:
                corrupted = response.text.strip()
                if corrupted and corrupted != chosen:
                    DPO_CACHE[chosen_hash] = corrupted
                    save_dpo_cache()
                    time.sleep(0.5)
                    return corrupted
        except Exception as e:
            logger.warning(
                f"Attempt {attempt + 1}/3 failed to generate DPO logical corruption via Gemini: {e}"
            )
            err_msg = str(e).upper()
            if (
                "RESOURCE_EXHAUSTED" in err_msg
                or "429" in err_msg
                or "UNAVAILABLE" in err_msg
                or "503" in err_msg
            ):
                sleep_time = (attempt + 1) * 15.0
                time.sleep(sleep_time)
            else:
                time.sleep(1.0)

    return corrupt_fact_substitution(chosen, language)


def compile_dpo_pairs(
    sft_path: str, output_path: str, limit: int = 2000, seed: int = 42
) -> int:
    """
    Lit le dataset SFT et la base Django, fusionne le feedback utilisateur,
    génère les paires DPO par corruption équilibrée, et les écrit au format JSONL.
    """
    random.seed(seed)

    # 1. Fetch real user feedback from Django database
    feedback_pairs = []
    try:
        from dpo_feedback_loop import DPOFeedbackLoop  # noqa: E402
    except ImportError:
        try:
            from backend.pipeline.mlops.dpo_feedback_loop import (  # noqa: E402
                DPOFeedbackLoop,
            )
        except ImportError:
            DPOFeedbackLoop = None

    if DPOFeedbackLoop:
        try:
            data_dir = os.path.dirname(output_path)
            loop = DPOFeedbackLoop(data_dir=data_dir)
            db_feedbacks = loop.fetch_db_feedbacks()

            # Helper callback for corruption of positive feedback
            def corrupt_callback(text):
                if random.random() < 0.5:
                    return corrupt_tonal_deviation(text)
                else:
                    return corrupt_evasive_refusal(text)

            for fb in db_feedbacks:
                if loop.validate_feedback(fb):
                    pair = loop.create_dpo_pair(fb, corrupt_callback)
                    if pair is not None:
                        feedback_pairs.append(pair)
            logger.info(
                f"Compiled {len(feedback_pairs)} DPO pairs from user feedback database."
            )
        except Exception as e:
            logger.warning(
                f"Failed to compile feedback pairs from Django database: {e}"
            )

    if not os.path.exists(sft_path):
        logger.error(f"SFT dataset not found at: {sft_path}")
        # If SFT is missing, still write feedback pairs if any
        if feedback_pairs:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as out_f:
                for pair in feedback_pairs[:limit]:
                    out_f.write(json.dumps(pair, ensure_ascii=False) + "\n")
            return min(len(feedback_pairs), limit)
        return 0

    logger.info(f"Reading SFT dataset from {sft_path}...")
    eligible_entries = []

    # Mots clés de refus à filtrer
    refusal_keywords = [
        "je ne peux pas",
        "je ne dispose pas",
        "désolé",
        "i cannot",
        "i don't have",
        "sorry",
    ]

    with open(sft_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if "instruction" not in entry or "output" not in entry:
                    continue

                output_text = entry["output"]
                instruction_text = entry["instruction"]

                if len(output_text) < 40:
                    continue

                if any(kw in output_text.lower() for kw in refusal_keywords) or any(
                    kw in instruction_text.lower() for kw in refusal_keywords
                ):
                    continue

                eligible_entries.append(entry)
            except json.JSONDecodeError:
                continue

    total_eligible = len(eligible_entries)
    logger.info(f"Found {total_eligible} eligible SFT entries for DPO conversion.")

    compiled_pairs = []
    compiled_pairs.extend(feedback_pairs)
    feedback_prompts = {p["prompt"] for p in feedback_pairs}

    remaining_limit = limit - len(compiled_pairs)
    if remaining_limit > 0:
        # Eligible SFT entries to process, excluding already compiled prompt contexts
        selected_entries = [
            e
            for e in eligible_entries
            if f"Génère une réponse expert pour : {e['instruction']}"
            not in feedback_prompts
            and e["instruction"] not in feedback_prompts
        ]
        random.shuffle(selected_entries)
        selected_entries = selected_entries[:remaining_limit]

        strategies = ["fact", "tone", "truncation", "refusal", "llm"]
        for idx, entry in enumerate(selected_entries):
            prompt = entry["instruction"]
            chosen = entry["output"]
            lang = entry.get("language", "Français")
            strategy = strategies[idx % len(strategies)]

            if strategy == "fact":
                rejected = corrupt_fact_substitution(chosen, lang)
            elif strategy == "tone":
                rejected = corrupt_tonal_deviation(chosen, lang)
            elif strategy == "truncation":
                rejected = corrupt_abrupt_truncation(chosen)
            elif strategy == "llm":
                rejected = corrupt_llm_critic(chosen, lang)
            else:
                rejected = corrupt_evasive_refusal(chosen, lang)

            if rejected == chosen:
                rejected = corrupt_evasive_refusal(chosen, lang)

            # Validate with Pydantic schema before appending
            try:
                validated = DPOSampleValidator(
                    prompt=prompt, chosen=chosen, rejected=rejected
                )
                compiled_pairs.append(validated.model_dump())
            except Exception as e:
                logger.warning(f"DPO sample dropped (validation failed): {e}")
    else:
        compiled_pairs = compiled_pairs[:limit]

    # Sauvegarder au format JSONL
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as out_f:
        for pair in compiled_pairs:
            out_f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    logger.info(
        f"Successfully compiled {len(compiled_pairs)} DPO pairs saved to {output_path}"
    )
    return len(compiled_pairs)


if __name__ == "__main__":
    # Paramètres via variables d'environnement
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    sft_default = os.path.join(
        base_dir, "data", "mlops", "datasets", "animetix_expert_ft.jsonl"
    )
    dpo_default = os.path.join(
        base_dir, "data", "mlops", "datasets", "dpo_train_validated.jsonl"
    )

    dpo_size = int(os.getenv("ANIMETIX_DPO_SIZE", "2000"))
    dpo_seed = int(os.getenv("ANIMETIX_DPO_SEED", "42"))

    compile_dpo_pairs(sft_default, dpo_default, limit=dpo_size, seed=dpo_seed)
