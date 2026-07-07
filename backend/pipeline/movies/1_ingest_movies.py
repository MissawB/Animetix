# Fix path for internal imports
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

import json  # noqa: E402
import logging  # noqa: E402
import os  # noqa: E402
import time  # noqa: E402

from core.utils.security import safe_http_request  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

# Configuration du logger
logger = logging.getLogger("animetix.pipeline.movies.ingest")

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "raw", "raw_tmdb_db.json")


def fetch_tmdb_page(endpoint, page=1, params={}):
    url = f"{BASE_URL}/{endpoint}"
    default_params = {"api_key": TMDB_API_KEY, "language": "fr-FR", "page": page}
    default_params.update(params)
    try:
        response = safe_http_request("GET", url, params=default_params, timeout=20)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            logger.warning("⚠️ Rate limit reached. Sleeping...")
            time.sleep(10)
            return fetch_tmdb_page(endpoint, page, params)
        return None
    except Exception as e:
        logger.error(f"❌ Error fetching TMDB page: {e}")
        return None


def ingest_movies():
    if not TMDB_API_KEY:
        logger.error("❌ TMDB_API_KEY not found in .env file.")
        return
    existing_data = []
    existing_ids = set()

    # Charger les données existantes
    if os.path.exists(OUTPUT_FILE):
        logger.info(f"📂 Loading existing data from {OUTPUT_FILE}...")
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                existing_ids = {item["id"] for item in existing_data}
            logger.info(f"✅ Found {len(existing_data)} existing items.")
        except Exception as e:
            logger.warning(f"⚠️ Could not load existing data: {e}")

    all_raw = []

    # On récupère 50 pages de chaque (50 * 20 = 1000 items par catégorie)
    logger.info("🎬 Collecting 1000+ candidate Movies & Series...")
    for page in range(1, 51):
        m = fetch_tmdb_page("movie/popular", page=page)
        if m:
            for item in m.get("results", []):
                item["media_type_custom"] = "Movie"
                all_raw.append(item)

        s = fetch_tmdb_page("tv/popular", page=page)
        if s:
            for item in s.get("results", []):
                genres = item.get("genre_ids", [])
                origin = item.get("origin_country", [])
                item["media_type_custom"] = (
                    "Cartoon" if (16 in genres and "JP" not in origin) else "Series"
                )
                all_raw.append(item)

        if page % 10 == 0:
            logger.info(f"   - Progress: {page}/50 pages collected...")
        time.sleep(0.1)

    # Tri par popularité et on regarde les candidats
    all_raw.sort(key=lambda x: x.get("popularity", 0), reverse=True)

    # On identifie ceux qu'on n'a pas encore enrichis
    new_candidates = [item for item in all_raw if item["id"] not in existing_ids]

    # Si on en a déjà beaucoup, on peut limiter les nouveaux à enrichir par session pour pas exploser le temps
    # Mais ici on va essayer d'enrichir tous les nouveaux trouvés dans le top scan
    limit_new = 500
    candidates_to_enrich = new_candidates[:limit_new]

    if not candidates_to_enrich:
        logger.info("ℹ️ No new items to enrich. Database is up to date.")
        return

    logger.info(
        f"✨ Enriching {len(candidates_to_enrich)} new items (Description, Cast, Keywords)..."
    )
    new_enriched_data = []
    for i, item in enumerate(candidates_to_enrich):
        m_type = "movie" if item["media_type_custom"] == "Movie" else "tv"
        details = fetch_tmdb_page(
            f"{m_type}/{item['id']}",
            params={"append_to_response": "credits,keywords,recommendations"},
        )

        if details:
            formatted = {
                "id": details.get("id"),
                "format": "MOVIE" if m_type == "movie" else "TV",
                "media_type": item["media_type_custom"],
                "popularity": details.get("popularity"),
                "title": details.get("title") or details.get("name"),
                "title_english": details.get("original_title")
                or details.get("original_name"),
                "title_native": details.get("original_title")
                or details.get("original_name"),
                "description": details.get("overview"),
                "genres": [g["name"] for g in details.get("genres", [])],
                "year": (
                    details.get("release_date")
                    or details.get("first_air_date")
                    or "0000"
                )[:4],
                "image": (
                    f"https://image.tmdb.org/t/p/w500{details.get('poster_path')}"
                    if details.get("poster_path")
                    else None
                ),
                "tags": [
                    k["name"]
                    for k in details.get("keywords", {}).get(
                        "keywords" if m_type == "movie" else "results", []
                    )
                ],
                "recommendations": {
                    r["title"] if m_type == "movie" else r["name"]: 50
                    for r in details.get("recommendations", {}).get("results", [])[:10]
                },
                "cast": [
                    c["name"] for c in details.get("credits", {}).get("cast", [])[:5]
                ],
            }
            new_enriched_data.append(formatted)

        if (i + 1) % 50 == 0:
            logger.info(f"📦 Enriched {i + 1}/{len(candidates_to_enrich)}...")
        time.sleep(0.1)

    # Fusion
    final_data = existing_data + new_enriched_data

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)

    logger.info(
        f"✅ Collection finished! Added {len(new_enriched_data)} new items. Total: {len(final_data)}"
    )


if __name__ == "__main__":
    ingest_movies()
