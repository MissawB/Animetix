import json
import logging
import os
import re
import sys

# Setup logging
logger = logging.getLogger("animetix." + __name__)

# Forcer l'encodage UTF-8 pour éviter les erreurs sur Windows avec les emojis
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# backend/pipeline/anime/<ce fichier> : trois dirname remontent à backend/, pas à la
# racine. Les modules du pipeline s'importent depuis backend/pipeline ; les données
# vivent à la racine du dépôt.
BACKEND_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
sys.path.append(os.path.join(BACKEND_DIR, "pipeline"))
from data_intelligence import intelligence_service  # noqa: E402

RAW_FILE = os.path.join(PROJECT_ROOT, "data", "raw", "raw_anilist_db.json")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data", "processed", "clean_root_animes.json")


def clean_description(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    patterns_to_remove = [
        r"\(Source:.*?\)",
        r"\[Written by.*?\]",
        r"Notes?:.*",
        r"Official website:.*",
        r"Originally aired.*",
        r"Adapted from.*",
        r"Based on the.*?manga.*",
        r"Included in.*",
        r"Winner of the.*?award.*",
    ]
    for pattern in patterns_to_remove:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    text = re.sub(r"https?://\S+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def build_clean_entry(anime, micro_tags):
    """The pure per-work transform: raw AniList media -> catalogue entry.

    `studios` used to be read from a key the GraphQL query never requested, so it
    was silently [] for every work. It is real now — and the quiz's studio, source
    and filiation archetypes read exactly these keys.
    """
    clean_tags = [t["name"] for t in anime.get("tags", []) if t.get("rank", 0) >= 70]

    relations = {}
    for edge in (anime.get("relations") or {}).get("edges", []):
        node_title = (edge.get("node") or {}).get("title", {}).get("romaji")
        if node_title:
            relations.setdefault(edge["relationType"], []).append(node_title)

    return {
        "id": anime["id"],
        "idMal": anime.get("idMal"),
        "title": anime["title"]["romaji"],
        "title_english": anime["title"]["english"],
        "title_native": anime["title"]["native"],
        "description": clean_description(anime.get("description")),
        "genres": anime["genres"],
        "tags": list(set(clean_tags + micro_tags)),
        "micro_tags": micro_tags,
        "popularity": anime["popularity"],
        "year": anime["startDate"]["year"] if anime["startDate"] else None,
        "image": anime["coverImage"]["large"] if anime["coverImage"] else None,
        "studios": [
            s["node"]["name"]
            for s in (anime.get("studios") or {}).get("edges", [])
            if s["node"].get("isAnimationStudio")
        ],
        "source": anime.get("source"),
        "episode_count": anime.get("episodes"),
        "relations": relations,
        "recommendations": (
            {
                r["mediaRecommendation"]["title"]["romaji"]: r["rating"]
                for r in anime["recommendations"]["nodes"]
                if r.get("mediaRecommendation")
            }
            if anime.get("recommendations")
            else {}
        ),
    }


def run_refinement():
    if not os.path.exists(RAW_FILE):
        logger.error(f"❌ Error: {RAW_FILE} not found.")
        return

    logger.info("Loading raw database...")
    with open(RAW_FILE, "r", encoding="utf-8") as f:
        all_animes = json.load(f)

    # Tri par popularité pour l'intelligence
    all_animes.sort(key=lambda x: x.get("popularity", 0), reverse=True)
    animes_map = {a["id"]: a for a in all_animes if a.get("description")}

    non_root_ids = set()
    RELATIONS_TO_EXCLUDE = [
        "PREQUEL",
        "REMAKE",
        "ALTERNATIVE_SETTING",
        "ALTERNATIVE_VERSION",
    ]
    for anime_id, anime in animes_map.items():
        if anime["format"] not in ["TV", "TV_SHORT"]:
            non_root_ids.add(anime_id)
            continue
        for edge in anime["relations"]["edges"]:
            if edge["relationType"] in RELATIONS_TO_EXCLUDE:
                non_root_ids.add(anime_id)
                break

    clean_root_animes = []
    processed_count = 0

    for anime_id, anime in animes_map.items():
        if anime_id not in non_root_ids:
            # --- DATA INTELLIGENCE (Top 200) ---
            micro_tags = []
            if processed_count < 200:
                try:
                    logger.info(
                        f"   🧠 Intelligence extraction [{processed_count + 1}/200]: {anime['title']['romaji']}..."
                    )
                    micro_tags = intelligence_service.extract_micro_tags(
                        anime["title"]["romaji"],
                        clean_description(anime.get("description")),
                        "Anime",
                    )
                except Exception as e:
                    logger.warning(
                        f"   ⚠️ Warning: Intelligence extraction failed for {anime['title']['romaji']}: {e}"
                    )
                    micro_tags = []

            clean_data = build_clean_entry(anime, micro_tags)

            # Construction des nœuds du graphe
            clean_data["graph_nodes"] = intelligence_service.build_relation_graph(
                clean_data, "Anime"
            )

            clean_root_animes.append(clean_data)
            processed_count += 1

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(clean_root_animes, f, indent=2, ensure_ascii=False)

    logger.info(
        f"✅ Intelligence Filtering Complete! Total: {len(clean_root_animes)} animes."
    )


if __name__ == "__main__":
    run_refinement()
