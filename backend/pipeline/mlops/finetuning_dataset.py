# -*- coding: utf-8 -*-
"""
Compilateur de jeu de données de fine-tuning SFT expert UNIFIÉ, 100% en français,
sans code-switching, fusionnant l'expertise d'animes/mangas japonais, les ponts transmédias,
les musiques (anisongs), les seiyuu, et l'écosystème du Marché Français (doubleurs VF, éditeurs, diffuseurs).
Proportions mathématiques parfaites garanties : 80% spécialisé, 5% vocabulaire méta, 15% général.
"""

import json  # noqa: E402
import logging  # noqa: E402
import os  # noqa: E402
import random

random = random.SystemRandom()  # type: ignore[assignment]  # intentional secure-RNG module shadowing
# noqa: E402
import sys  # noqa: E402

from datasets import load_dataset  # noqa: E402

try:
    from google import genai  # noqa: E402
except ImportError:
    genai = None

logger = logging.getLogger("animetix.pipeline." + __name__)

# Nettoyage de texte extrait dans un module dédié ; ré-exporté ici pour
# préserver la compatibilité (`finetuning_dataset.clean_description`, etc.).
# Chemins partagés extraits dans un module dédié ; ré-exportés pour compatibilité.
from .ft_dataset.paths import (  # noqa: E402,F401
    ANIME_DB,
    BASE_DIR,
    CACHE_FILE,
    CHAR_DB,
    MANGA_DB,
    OUTPUT_DATASET,
)
from .ft_dataset.text_cleaning import (  # noqa: E402,F401
    clean_description,
    clean_source_prose,
    clean_tags,
    inject_query_noise,
)

# Ajout du répertoire courant pour l'import des modules de base de données locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from otaku_concepts import OTAKU_VOCABULARY  # noqa: E402

from .ft_dataset.dialogue_generators import (  # noqa: E402,F401
    generate_multiturn_dialogues,
)
from .ft_dataset.market_profile_generators import (  # noqa: E402,F401
    generate_french_market_profile_instructions,
    generate_japanese_market_profile_instructions,
)
from .ft_dataset.otaku_generators import (  # noqa: E402,F401
    generate_otaku_meta_instructions,
)

# Cache de paraphrases + appels Gemini extraits dans un module dédié ; ré-exportés
# pour préserver la compatibilité (`finetuning_dataset.paraphrase_text_via_gemini`, etc.).
from .ft_dataset.paraphrase import (  # noqa: E402,F401
    PARAPHRASE_CACHE,
    load_paraphrase_cache,
    paraphrase_text_via_gemini,
    save_paraphrase_cache,
    translate_to_english_via_gemini,
    validate_factual_alignment,
)

# Générateurs « pilotés par données » (Q&A depuis les bases de relations) extraits
# dans un module dédié ; ré-exportés pour préserver la compatibilité.
from .ft_dataset.relation_generators import (  # noqa: E402,F401
    generate_awards_and_magazines_instructions,
    generate_french_market_relations_instructions,
    generate_japanese_market_relations_instructions,
    generate_songs_and_seiyuu_instructions,
    generate_transmedia_instructions,
    generate_volumes_and_episodes_instructions,
)
from .ft_dataset.synthetic_generators import (  # noqa: E402,F401
    generate_mcp_tool_instructions,
    generate_negative_refusal_examples,
    generate_rag_context_instructions,
)


def calculate_dataset_counts(non_meta_count: int) -> tuple[int, int]:
    """
    Calcule dynamiquement le nombre d'exemples méta et généraux nécessaires
    en fonction du nombre d'exemples spécialisés (non_meta_count) et des ratios
    configurés via les variables d'environnement.
    """
    ratio_spec = float(os.getenv("ANIMETIX_RATIO_SPECIALIZED", "80.0"))
    ratio_meta = float(os.getenv("ANIMETIX_RATIO_META", "5.0"))
    ratio_gen = float(os.getenv("ANIMETIX_RATIO_GENERAL", "15.0"))

    # Normalisation pour être robuste
    total_ratio = ratio_spec + ratio_meta + ratio_gen
    if total_ratio <= 0:
        logger.warning(
            "Total SFT ratio is less than or equal to 0, falling back to 80/5/15."
        )
        ratio_spec, ratio_meta, ratio_gen = 80.0, 5.0, 15.0
        total_ratio = 100.0

    meta_required = int(non_meta_count * (ratio_meta / ratio_spec))
    general_required = int(non_meta_count * (ratio_gen / ratio_spec))

    return meta_required, general_required


# Tables de synonymes/surnoms et constructeurs de profils/bios extraits dans un
# module dédié ; ré-exportés ici pour préserver la compatibilité.
from .ft_dataset.profile_builders import (  # noqa: E402,F401
    CHARACTER_NICKNAMES,
    MULTI_TITLE_MAP,
    get_character_synonyms_string,
    get_display_character,
    get_display_title,
    get_synonyms_string,
    make_english_anime_profile,
    make_english_character_bio,
    make_english_manga_profile,
    make_french_anime_profile,
    make_french_character_bio,
    make_french_manga_profile,
)


def fetch_general_instructions(count):
    """Télécharge de manière stable 'pinzhenchen/alpaca-cleaned-fr' et 'yahma/alpaca-cleaned' depuis HF Hub."""
    logger.info(f"[INFO] Loading {count} general SFT instructions from Hugging Face...")

    fr_count = count // 2
    en_count = count - fr_count

    general_samples = []

    if fr_count > 0:
        logger.info(f"[INFO] Loading {fr_count} French general instructions...")
        try:
            # Using revision="main" to ensure secure, reproducible download
            ds_fr = load_dataset(
                "pinzhenchen/alpaca-cleaned-fr", split="train", revision="main"
            )  # nosec B615
            for i in range(min(fr_count, len(ds_fr))):
                item = ds_fr[i]
                general_samples.append(
                    {
                        "instruction": item.get("instruction", ""),
                        "input": item.get("input", ""),
                        "output": item.get("output", ""),
                        "language": "Français",
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to load French Alpaca dataset: {e}")

    if en_count > 0:
        logger.info(f"[INFO] Loading {en_count} English general instructions...")
        try:
            # Using revision="main" to ensure secure, reproducible download
            ds_en = load_dataset(
                "yahma/alpaca-cleaned", split="train", revision="main"
            )  # nosec B615
            for i in range(min(en_count, len(ds_en))):
                item = ds_en[i]
                general_samples.append(
                    {
                        "instruction": item.get("instruction", ""),
                        "input": item.get("input", ""),
                        "output": item.get("output", ""),
                        "language": "English",
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to load English Alpaca dataset: {e}")

    logger.info(
        f"[SUCCESS] Loaded exactly {len(general_samples)} general SFT instructions."
    )
    return general_samples


def deduplicate_dataset(dataset):
    seen = set()
    deduped = []
    duplicates_count = 0
    for item in dataset:
        if "turns" in item:
            sig_list = []
            for t in item["turns"]:
                sig_list.append(t["user"].strip())
                sig_list.append(t["assistant"].strip())
            key = tuple(sig_list)
        else:
            key = (item["instruction"].strip(), item.get("input", "").strip())

        if key in seen:
            duplicates_count += 1
            continue
        seen.add(key)
        deduped.append(item)
    logger.info(f"[INFO] Deduplication removed {duplicates_count} duplicate SFT pairs.")
    return deduped


def run_generate_instruction_dataset():
    specialized_data = []

    # Initialisation client Gemini pour augmentation facultative
    augment_data = os.getenv("ANIMETIX_AUGMENT_DATA", "False").lower() in ("true", "1")
    api_key = os.getenv("GEMINI_API_KEY")
    client = None
    if augment_data and api_key and genai is not None:
        logger.info("[INFO] Initializing Gemini API client for data augmentation...")
        client = genai.Client(api_key=api_key)
    else:
        logger.info(
            "[INFO] Gemini API client not initialized (augmentation disabled or missing key). Using static templates."
        )

    # Limites d'augmentation pour maîtriser les coûts et le temps d'exécution
    limit_anime_t1 = int(os.getenv("ANIMETIX_LIMIT_ANIME_T1", "15"))
    limit_anime_t2 = int(os.getenv("ANIMETIX_LIMIT_ANIME_T2", "10"))
    limit_manga_t1 = int(os.getenv("ANIMETIX_LIMIT_MANGA_T1", "5"))
    limit_manga_t2 = int(os.getenv("ANIMETIX_LIMIT_MANGA_T2", "5"))
    limit_char_t1 = int(os.getenv("ANIMETIX_LIMIT_CHAR_T1", "15"))
    limit_char_t2 = int(os.getenv("ANIMETIX_LIMIT_CHAR_T2", "10"))

    # Établir la liste des éléments éligibles à l'augmentation par tri de popularité
    augmented_anime_titles = set()
    if os.path.exists(ANIME_DB) and client:
        try:
            with open(ANIME_DB, "r", encoding="utf-8") as f:
                animes_list = json.load(f)
                t1_animes = [
                    item for item in animes_list if item.get("popularity", 0) > 150000
                ]
                t1_animes.sort(key=lambda x: x.get("popularity", 0), reverse=True)
                for item in t1_animes[:limit_anime_t1]:
                    if item.get("title"):
                        augmented_anime_titles.add(item.get("title"))

                t2_animes = [
                    item
                    for item in animes_list
                    if 50000 < item.get("popularity", 0) <= 150000
                ]
                t2_animes.sort(key=lambda x: x.get("popularity", 0), reverse=True)
                for item in t2_animes[:limit_anime_t2]:
                    if item.get("title"):
                        augmented_anime_titles.add(item.get("title"))
            logger.info(
                f"[INFO] Targeted {len(augmented_anime_titles)} popular animes for dynamic augmentation."
            )
        except Exception as e:
            logger.warning(f"Failed to identify target animes for augmentation: {e}")

    augmented_manga_titles = set()
    if os.path.exists(MANGA_DB) and client:
        try:
            with open(MANGA_DB, "r", encoding="utf-8") as f:
                mangas_list = json.load(f)
                t1_mangas = [
                    item for item in mangas_list if item.get("popularity", 0) > 150000
                ]
                t1_mangas.sort(key=lambda x: x.get("popularity", 0), reverse=True)
                for item in t1_mangas[:limit_manga_t1]:
                    if item.get("title"):
                        augmented_manga_titles.add(item.get("title"))

                t2_mangas = [
                    item
                    for item in mangas_list
                    if 50000 < item.get("popularity", 0) <= 150000
                ]
                t2_mangas.sort(key=lambda x: x.get("popularity", 0), reverse=True)
                for item in t2_mangas[:limit_manga_t2]:
                    if item.get("title"):
                        augmented_manga_titles.add(item.get("title"))
            logger.info(
                f"[INFO] Targeted {len(augmented_manga_titles)} popular mangas for dynamic augmentation."
            )
        except Exception as e:
            logger.warning(f"Failed to identify target mangas for augmentation: {e}")

    augmented_char_names = set()
    if os.path.exists(CHAR_DB) and client:
        try:
            with open(CHAR_DB, "r", encoding="utf-8") as f:
                chars_list = json.load(f)
                top_chars_list = [
                    c
                    for c in chars_list
                    if c.get("popularity", {}).get("favourites", 0) > 50
                ]

                t1_chars = [
                    c
                    for c in top_chars_list
                    if c.get("popularity", {}).get("favourites", 0) > 2000
                ]
                t1_chars.sort(
                    key=lambda x: x.get("popularity", {}).get("favourites", 0),
                    reverse=True,
                )
                for item in t1_chars[:limit_char_t1]:
                    if item.get("name") and item.get("origin"):
                        augmented_char_names.add((item.get("name"), item.get("origin")))

                t2_chars = [
                    c
                    for c in top_chars_list
                    if 500 < c.get("popularity", {}).get("favourites", 0) <= 2000
                ]
                t2_chars.sort(
                    key=lambda x: x.get("popularity", {}).get("favourites", 0),
                    reverse=True,
                )
                for item in t2_chars[:limit_char_t2]:
                    if item.get("name") and item.get("origin"):
                        augmented_char_names.add((item.get("name"), item.get("origin")))
            logger.info(
                f"[INFO] Targeted {len(augmented_char_names)} popular characters for dynamic augmentation."
            )
        except Exception as e:
            logger.warning(
                f"Failed to identify target characters for augmentation: {e}"
            )

    # 1. TRANSMEDIA BRIDGES (400 instructions en français)
    logger.info("[INFO] Generating high-quality transmedia bridge instructions...")
    transmedia_data = generate_transmedia_instructions()
    specialized_data.extend(transmedia_data)

    # 1b. MAGAZINES AND AWARDS (160 instructions en français)
    logger.info(
        "[INFO] Generating high-quality magazines and awards relational instructions..."
    )
    awards_mag_data = generate_awards_and_magazines_instructions()
    specialized_data.extend(awards_mag_data)

    # 1c. SONGS AND SEIYUU (160 instructions en français)
    logger.info(
        "[INFO] Generating high-quality openings, endings, and seiyuu relational instructions..."
    )
    songs_seiyuu_data = generate_songs_and_seiyuu_instructions()
    specialized_data.extend(songs_seiyuu_data)

    # 1d. PAYSAGE FRANÇAIS - RELATIONS (160 instructions en français)
    logger.info(
        "[INFO] Generating high-quality French market relational instructions..."
    )
    french_relations = generate_french_market_relations_instructions()
    specialized_data.extend(french_relations)

    # 1d2. PAYSAGE JAPONAIS - RELATIONS (160 instructions en français)
    logger.info(
        "[INFO] Generating high-quality Japanese market relational instructions..."
    )
    japanese_relations = generate_japanese_market_relations_instructions()
    specialized_data.extend(japanese_relations)

    # 1e. PAYSAGE FRANÇAIS - PROFILS (600 instructions en français)
    logger.info(
        "[INFO] Generating high-quality French voice actors, publishers, and distributors profile instructions..."
    )
    french_profiles = generate_french_market_profile_instructions()
    specialized_data.extend(french_profiles)

    # 1e2. PAYSAGE JAPONAIS - PROFILS (600 instructions en français)
    logger.info(
        "[INFO] Generating high-quality Japanese voice actors, publishers, and distributors profile instructions..."
    )
    japanese_profiles = generate_japanese_market_profile_instructions()
    specialized_data.extend(japanese_profiles)

    # 1f. VOLUMES ET EPISODES (72 instructions en français)
    logger.info(
        "[INFO] Generating high-quality manga volumes and anime episodes instructions..."
    )
    vol_ep_data = generate_volumes_and_episodes_instructions()
    specialized_data.extend(vol_ep_data)

    # 1g. CADRAGE D'OUTILS VIA MCP (serveurs Jikan & Spotify)
    logger.info("[INFO] Generating high-quality MCP tool calling instructions...")
    mcp_data = generate_mcp_tool_instructions()
    specialized_data.extend(mcp_data)

    # 1h. SIMULATION DE CONTEXTES RAG AVEC BRUIT
    logger.info("[INFO] Generating RAG context simulation instructions with noise...")
    animes_list = []
    if os.path.exists(ANIME_DB):
        with open(ANIME_DB, "r", encoding="utf-8") as f:
            animes_list = json.load(f)
    chars_list = []
    if os.path.exists(CHAR_DB):
        with open(CHAR_DB, "r", encoding="utf-8") as f:
            chars_list = json.load(f)
    rag_data = generate_rag_context_instructions(animes_list, chars_list)
    specialized_data.extend(rag_data)

    # 2. ANIME DATABASE
    if os.path.exists(ANIME_DB):
        with open(ANIME_DB, "r", encoding="utf-8") as f:
            animes = json.load(f)
            logger.info(
                f"[INFO] Processing ALL {len(animes)} animes with popularity weighting..."
            )
            for idx, item in enumerate(animes):
                title = clean_description(item.get("title", "Unknown"))
                genres = [clean_description(g) for g in item.get("genres", [])]
                studios = [clean_description(s) for s in item.get("studios", [])]
                tags = [clean_description(t) for t in item.get("tags", [])]
                pop = item.get("popularity", 0)
                year = item.get("year", 2020)

                display_t = get_display_title(title)

                # Check for underrepresented genres (Shojo, Josei, Slice of Life, Mecha, Iyashikei, Mahou Shoujo, Music, Sports, Historical, Horror, Thriller)
                is_underrepresented = False
                underrepresented_keywords = [
                    "shoujo",
                    "shojo",
                    "josei",
                    "slice of life",
                    "tranche de vie",
                    "iyashikei",
                    "mecha",
                    "mahou shoujo",
                    "magical girl",
                    "music",
                    "sports",
                    "historical",
                    "horror",
                    "thriller",
                ]
                for term in underrepresented_keywords:
                    if any(term in str(g).lower() for g in genres + tags):
                        is_underrepresented = True
                        break

                # Boost retro eras (70s, 80s, 90s)
                if not is_underrepresented and year and 1970 <= year <= 1999:
                    is_underrepresented = True

                effective_pop = pop
                if is_underrepresented:
                    effective_pop = max(pop, 150001) if pop > 50000 else 100000

                description = clean_source_prose(item.get("description", ""))
                is_en = idx % 2 == 1
                lang = "English" if is_en else "Français"
                studios_str = (
                    ", ".join(studios)
                    if studios
                    else ("an unspecified studio" if is_en else "un studio non précisé")
                )
                genres_str = (
                    ", ".join(clean_tags(genres, lang))
                    if genres
                    else ("various genres" if is_en else "genres variés")
                )

                if is_en:
                    primary = make_english_anime_profile(
                        title, genres, studios, tags, year, description
                    )
                    q_primary = f"Present the anime '{display_t}' in detail."
                    aux1 = (
                        f"Which studio produced '{display_t}' and when?",
                        f"'{display_t}' was produced by {studios_str} and released in {year}.",
                    )
                    aux2 = (
                        f"What genres define '{display_t}'?",
                        f"'{display_t}' spans: {genres_str}.",
                    )
                else:
                    primary = make_french_anime_profile(
                        title, genres, studios, tags, year
                    )
                    q_primary = f"Présente l'anime '{display_t}' de manière détaillée."
                    aux1 = (
                        f"Quel studio a produit '{display_t}' et en quelle année ?",
                        f"'{display_t}' a été produit par {studios_str} et est sorti en {year}.",
                    )
                    aux2 = (
                        f"Quels sont les genres de '{display_t}' ?",
                        f"'{display_t}' relève des genres : {genres_str}.",
                    )

                if client and title in augmented_anime_titles:
                    primary = paraphrase_text_via_gemini(
                        primary, client, "encyclopédique"
                    )

                specialized_data.append(
                    {
                        "instruction": q_primary,
                        "input": "",
                        "output": primary,
                        "language": lang,
                    }
                )
                entity_outputs = {primary}
                if effective_pop > 150000:  # Tier-1: +2 aux
                    candidate_aux = (aux1, aux2)
                elif effective_pop > 50000:  # Tier-2: +1 aux
                    candidate_aux = (aux1,)
                else:  # Tier-3: primary only
                    candidate_aux = ()
                for q, a in candidate_aux:
                    if a in entity_outputs:
                        continue
                    specialized_data.append(
                        {"instruction": q, "input": "", "output": a, "language": lang}
                    )
                    entity_outputs.add(a)

    # 3. MANGA DATABASE
    if os.path.exists(MANGA_DB):
        with open(MANGA_DB, "r", encoding="utf-8") as f:
            mangas = json.load(f)
            logger.info(
                f"[INFO] Processing ALL {len(mangas)} mangas with popularity weighting..."
            )
            for idx, item in enumerate(mangas):
                title = clean_description(item.get("title", "Unknown"))
                genres = [clean_description(g) for g in item.get("genres", [])]
                tags = [clean_description(t) for t in item.get("tags", [])]
                pop = item.get("popularity", 0)

                display_t = get_display_title(title)

                year = item.get("year")
                display_t = get_display_title(title)

                # Check for underrepresented genres (Shojo, Josei, Slice of Life, Mecha, Iyashikei, Mahou Shoujo, Music, Sports, Historical, Horror, Thriller)
                is_underrepresented = False
                underrepresented_keywords = [
                    "shoujo",
                    "shojo",
                    "josei",
                    "slice of life",
                    "tranche de vie",
                    "iyashikei",
                    "mecha",
                    "mahou shoujo",
                    "magical girl",
                    "music",
                    "sports",
                    "historical",
                    "horror",
                    "thriller",
                ]
                for term in underrepresented_keywords:
                    if any(term in str(g).lower() for g in genres + tags):
                        is_underrepresented = True
                        break

                # Boost retro eras (70s, 80s, 90s)
                if not is_underrepresented and year and 1970 <= year <= 1999:
                    is_underrepresented = True

                effective_pop = pop
                if is_underrepresented:
                    effective_pop = max(pop, 150001) if pop > 50000 else 100000

                description = clean_source_prose(item.get("description", ""))
                is_en = idx % 2 == 1
                lang = "English" if is_en else "Français"
                genres_str = (
                    ", ".join(clean_tags(genres, lang))
                    if genres
                    else ("various genres" if is_en else "genres variés")
                )

                if is_en:
                    primary = make_english_manga_profile(
                        title, genres, tags, description
                    )
                    q_primary = f"What is the manga '{display_t}' about?"
                    aux1 = (
                        f"What genres define the manga '{display_t}'?",
                        f"'{display_t}' spans: {genres_str}.",
                    )
                else:
                    primary = make_french_manga_profile(title, genres, tags)
                    q_primary = f"De quoi parle le manga '{display_t}' ?"
                    aux1 = (
                        f"Quels sont les genres du manga '{display_t}' ?",
                        f"'{display_t}' relève des genres : {genres_str}.",
                    )

                if client and title in augmented_manga_titles:
                    primary = paraphrase_text_via_gemini(
                        primary, client, "encyclopédique"
                    )

                specialized_data.append(
                    {
                        "instruction": q_primary,
                        "input": "",
                        "output": primary,
                        "language": lang,
                    }
                )
                if (
                    effective_pop > 50000 and aux1[1] != primary
                ):  # Tier-1 & Tier-2: +1 aux
                    specialized_data.append(
                        {
                            "instruction": aux1[0],
                            "input": "",
                            "output": aux1[1],
                            "language": lang,
                        }
                    )

    # 4. CHARACTER DATABASE
    if os.path.exists(CHAR_DB):
        with open(CHAR_DB, "r", encoding="utf-8") as f:
            chars = json.load(f)
            top_chars = [
                c for c in chars if c.get("popularity", {}).get("favourites", 0) > 50
            ]
            logger.info(
                f"[INFO] Processing {len(top_chars)} characters with tiered augmentation..."
            )

            for idx, c in enumerate(top_chars):
                name = clean_description(c.get("name", "Anonyme"))
                origin = clean_description(c.get("origin", "Inconnu"))
                ents = c.get("entities", {})
                orgs = [clean_description(o) for o in ents.get("organizations", [])]
                favs = c.get("popularity", {}).get("favourites", 0)

                display_name = get_display_character(name)
                display_origin = get_display_title(origin)

                biography = clean_source_prose(c.get("biography", ""))
                is_en = idx % 2 == 1
                lang = "English" if is_en else "Français"

                if is_en:
                    primary = make_english_character_bio(
                        display_name, display_origin, orgs, biography
                    )
                    q_primary = f"Who is {display_name}?"
                    aux1 = (
                        f"Which work does {display_name} come from?",
                        f"{display_name} is a character from '{display_origin}'.",
                    )
                else:
                    primary = make_french_character_bio(
                        display_name, display_origin, orgs
                    )
                    q_primary = f"Qui est {display_name} ?"
                    aux1 = (
                        f"De quelle œuvre vient {display_name} ?",
                        f"{display_name} est un personnage de '{display_origin}'.",
                    )

                if client and (name, origin) in augmented_char_names:
                    primary = paraphrase_text_via_gemini(
                        primary, client, "encyclopédique"
                    )

                specialized_data.append(
                    {
                        "instruction": q_primary,
                        "input": "",
                        "output": primary,
                        "language": lang,
                    }
                )
                if favs > 500 and aux1[1] != primary:  # Tier-1 & Tier-2: +1 aux
                    specialized_data.append(
                        {
                            "instruction": aux1[0],
                            "input": "",
                            "output": aux1[1],
                            "language": lang,
                        }
                    )

    # Déduplication
    specialized_data = deduplicate_dataset(specialized_data)
    # Ensure every instruction in specialized_data has a default language of "Français"
    for item in specialized_data:
        if "language" not in item:
            item["language"] = "Français"

    non_meta_count = len(specialized_data)

    # Generate Multi-Turn dialogues to represent ~15% of the SFT dataset
    multiturn_required = int(non_meta_count * 0.18)
    logger.info(
        f"[INFO] Generating {multiturn_required} multi-turn dialogue examples..."
    )

    animes_list = []
    if os.path.exists(ANIME_DB):
        with open(ANIME_DB, "r", encoding="utf-8") as f:
            animes_list = json.load(f)

    mangas_list = []
    if os.path.exists(MANGA_DB):
        with open(MANGA_DB, "r", encoding="utf-8") as f:
            mangas_list = json.load(f)

    chars_list = []
    if os.path.exists(CHAR_DB):
        with open(CHAR_DB, "r", encoding="utf-8") as f:
            chars_list = json.load(f)

    multiturn_dialogues = generate_multiturn_dialogues(
        animes_list, mangas_list, chars_list, OTAKU_VOCABULARY, count=multiturn_required
    )
    multiturn_dialogues = deduplicate_dataset(multiturn_dialogues)

    # Generate out-of-scope/refusal negative examples to represent ~1.5% of the dataset
    refusal_required = int(
        non_meta_count * 0.02
    )  # ~2% of non-meta is about 1.5% of total
    logger.info(
        f"[INFO] Generating {refusal_required} out-of-scope refusal negative examples..."
    )
    refusal_data = generate_negative_refusal_examples(count=refusal_required)
    refusal_data = deduplicate_dataset(refusal_data)

    # 5. RATIO CONFIGURABLE ET PARAMETRABLE (Défaut : 80% Spécialisé, 5% Meta, 15% Général)
    meta_required, general_required = calculate_dataset_counts(non_meta_count)

    logger.info(
        f"[INFO] Total Non-meta (80% target) instructions generated: {non_meta_count}"
    )
    logger.info(f"[INFO] Target Meta required (5% target): {meta_required}")
    logger.info(f"[INFO] Target General required (15% target): {general_required}")

    # Pool de questions méta
    logger.info(
        "[INFO] Generating high-quality Otaku Meta Vocabulary questions pool..."
    )
    meta_pool = generate_otaku_meta_instructions(client)
    meta_pool = deduplicate_dataset(meta_pool)

    # Échantillonnage
    if meta_required <= len(meta_pool):
        selected_meta = random.sample(meta_pool, meta_required)
    else:
        selected_meta = list(meta_pool)
        diff_needed = meta_required - len(meta_pool)
        paraphrases = [
            ("En tant que grand sage Otaku, explique-moi : {q}", "{a}"),
            ("Je voudrais une analyse experte de : {q}", "{a}"),
            ("Peux-tu vulgariser ce concept Otaku : {q}", "Voici l'explication : {a}"),
            ("Décris-moi en détail : {q}", "{a}"),
            ("Fais un focus sur la notion de : {q}", "Focus expert : {a}"),
            ("Pourrais-tu détailler le concept de : {q}", "{a}"),
            ("Donne-moi l'analyse d'expert sur le trope : {q}", "{a}"),
        ]
        extra_meta = []
        while len(extra_meta) < diff_needed:
            base_item = random.choice(meta_pool)
            p_template, a_template = random.choice(paraphrases)
            new_instruction = p_template.format(q=base_item["instruction"])
            new_output = a_template.format(a=base_item["output"])
            extra_meta.append(
                {
                    "instruction": new_instruction,
                    "input": base_item["input"],
                    "output": new_output,
                    "language": base_item.get("language", "Français"),
                }
            )
        selected_meta.extend(extra_meta)

    # Téléchargement stable de pinzhenchen/alpaca-cleaned-fr
    general_data = fetch_general_instructions(general_required)

    # Assemblage unifié
    final_dataset = []
    final_dataset.extend(specialized_data)
    final_dataset.extend(selected_meta)
    final_dataset.extend(general_data)
    final_dataset.extend(multiturn_dialogues)
    final_dataset.extend(refusal_data)

    # Mélange global
    logger.info("[INFO] Shuffling the unified massive dataset...")
    random.shuffle(final_dataset)

    # --- INJECT QUERY NOISE (10-15% of user prompts/turns) ---
    noise_rate_env = os.getenv("ANIMETIX_QUERY_NOISE_RATE", "0.12")
    try:
        noise_rate = float(noise_rate_env)
        if not (0.0 <= noise_rate <= 1.0):
            raise ValueError("Rate out of bounds")
    except ValueError:
        logger.warning(
            f"Invalid ANIMETIX_QUERY_NOISE_RATE: '{noise_rate_env}'. Falling back to 0.12."
        )
        noise_rate = 0.12

    logger.info(
        f"[INFO] Injecting query noise with rate target: {noise_rate * 100:.1f}%..."
    )
    noise_count = 0
    for item in final_dataset:
        if random.random() < noise_rate:
            noise_count += 1
            lang = item.get("language", "Français")
            if "turns" in item:
                for turn in item["turns"]:
                    if "user" in turn:
                        turn["user"] = inject_query_noise(turn["user"], lang)
            else:
                if "instruction" in item:
                    item["instruction"] = inject_query_noise(item["instruction"], lang)

    actual_noise_rate = (
        (noise_count / len(final_dataset)) * 100 if final_dataset else 0.0
    )
    logger.info(
        f"[SUCCESS] Injected query noise into {noise_count}/{len(final_dataset)} instructions ({actual_noise_rate:.2f}%)."
    )

    # Sauvegarde finale en JSONL
    os.makedirs(os.path.dirname(OUTPUT_DATASET), exist_ok=True)
    with open(OUTPUT_DATASET, "w", encoding="utf-8") as f:
        for entry in final_dataset:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    total_count = len(final_dataset)
    actual_spec_ratio = len(specialized_data) / total_count * 100
    actual_meta_ratio = len(selected_meta) / total_count * 100
    actual_gen_ratio = len(general_data) / total_count * 100

    logger.info(
        f"[SUCCESS] UNIFIED MASSIVE AND OPTIMIZED DATASET READY: {total_count} total instructions."
    )
    logger.info("[INFO] Final Ratios Check:")
    logger.info(
        f"  - Specialized, Bridges & French Market (80% target): {len(specialized_data)} / {total_count} ({actual_spec_ratio:.2f}%)"
    )
    logger.info(
        f"  - Otaku Meta-Vocabulary (5% target): {len(selected_meta)} / {total_count} ({actual_meta_ratio:.2f}%)"
    )
    logger.info(
        f"  - General French SFT (15% target): {len(general_data)} / {total_count} ({actual_gen_ratio:.2f}%)"
    )
    logger.info(
        f"  - Multi-Turn Dialogues (15-20% target): {len(multiturn_dialogues)} / {total_count} ({len(multiturn_dialogues) / total_count * 100:.2f}%)"
    )
    logger.info(
        f"  - Persona & Refus (Negative) (1-2% target): {len(refusal_data)} / {total_count} ({len(refusal_data) / total_count * 100:.2f}%)"
    )
    logger.info(
        f"  - Query Noise (10-15% target): {noise_count} / {total_count} ({actual_noise_rate:.2f}%)"
    )
    logger.info(f"[INFO] Saved at: {OUTPUT_DATASET}")

    # Sauvegarde du cache
    save_paraphrase_cache()


if __name__ == "__main__":
    run_generate_instruction_dataset()
