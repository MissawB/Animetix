import json
import time
import os
import sys
import logging

# Fix path for internal imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

from core.utils.security import safe_http_request  # noqa: E402

logger = logging.getLogger("animetix." + __name__)

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ANIME_INPUT = os.path.join(BASE_DIR, "data", "raw", "raw_anilist_db.json")
MANGA_INPUT = os.path.join(BASE_DIR, "data", "raw", "raw_anilist_manga_db.json")
CHAR_INPUT = os.path.join(BASE_DIR, "data", "raw", "raw_characters_db.json")

ANIME_OUTPUT = os.path.join(BASE_DIR, "data", "raw", "jikan_anime_enrichment.json")
MANGA_OUTPUT = os.path.join(BASE_DIR, "data", "raw", "jikan_manga_enrichment.json")
CHAR_OUTPUT = os.path.join(BASE_DIR, "data", "raw", "jikan_char_enrichment.json")


def fetch_jikan_details(mal_id, media_type="anime"):
    url = f"https://api.jikan.moe/v4/{media_type}/{mal_id}/full"
    try:
        response = safe_http_request("GET", url, timeout=15)
        if response.status_code == 200:
            return response.json().get("data", {})
        elif response.status_code == 429:
            logger.warning(
                f"⚠️ Rate limit reached for {media_type} {mal_id}. Sleeping 10s..."
            )
            time.sleep(10)
            return fetch_jikan_details(mal_id, media_type)
        else:
            return {}
    except Exception as e:
        logger.error(f"❌ Exception for {media_type} {mal_id} details: {e}")
        return {}


def fetch_jikan_recommendations(mal_id, media_type="anime"):
    url = f"https://api.jikan.moe/v4/{media_type}/{mal_id}/recommendations"
    try:
        response = safe_http_request("GET", url, timeout=15)
        if response.status_code == 200:
            return response.json().get("data", [])
        elif response.status_code == 429:
            time.sleep(10)
            return fetch_jikan_recommendations(mal_id, media_type)
        return []
    except Exception as e:
        logger.warning(f"⚠️ Error fetching recommendations for {mal_id}: {e}")
        return []


def enrich_media(input_file, output_file, media_type="anime"):
    if not os.path.exists(input_file):
        logger.info(f"Skipping {media_type}: {input_file} not found.")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    enrichment_data = {}
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                enrichment_data = json.load(f)
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors du chargement de {output_file}: {e}")
            pass

    logger.info(f"🚀 Enriching {len(data)} {media_type}s using Jikan...")

    count = 0
    # On limite à 1000 items pour éviter de saturer l'API Jikan pendant des heures
    # Vous pouvez augmenter cette limite si nécessaire
    for item in data[:1000]:
        mal_id = item.get("idMal")
        if not mal_id or str(mal_id) in enrichment_data:
            continue

        # 1. Fetch Details
        details = fetch_jikan_details(mal_id, media_type)
        time.sleep(1.2)  # Jikan limit: 3 requests per second max

        # 2. Fetch Recommendations
        recs = fetch_jikan_recommendations(mal_id, media_type)

        if details or recs:
            # SÉCURISATION : Utilisation de .get() pour éviter KeyError: 'content'
            clean_recs = []
            for r in recs:
                entry = r.get("entry", {})
                clean_recs.append(
                    {
                        "title": entry.get("title", "Unknown"),
                        "content": r.get("content", ""),  # C'est ici que ça plantait
                    }
                )

            enrichment_data[str(mal_id)] = {
                "synopsis_en": details.get("synopsis"),
                "synopsis_fr": None,  # Jikan ne fournit pas le français nativement
                "alternative_titles": [
                    t.get("title") for t in details.get("titles", []) if t.get("title")
                ],
                "background": details.get("background"),
                "themes": [
                    t.get("name") for t in details.get("themes", []) if "name" in t
                ],
                "recommendations": clean_recs,
            }

        count += 1
        if count % 20 == 0:
            logger.info(f"✅ Processed {count} items...")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(enrichment_data, f, indent=2, ensure_ascii=False)

        time.sleep(1.2)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(enrichment_data, f, indent=2, ensure_ascii=False)

    logger.info(f"✅ Finished enriching {media_type}s!")


def enrich_characters(input_file, output_file):
    if not os.path.exists(input_file):
        return

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                json.load(f)
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors du chargement de {output_file}: {e}")
            pass

    logger.info(f"🚀 Enriching {len(data)} characters using Jikan...")

    for item in data[:500]:
        item.get("id")  # AniList ID
        # Pour les persos, on tente de trouver l'équivalent Jikan si possible
        # Note: L'enrichissement des persos par Jikan est plus complexe car les IDs diffèrent
        continue  # Optionnel pour l'instant pour gagner du temps

    logger.info("✅ Character enrichment step completed.")


if __name__ == "__main__":
    os.makedirs(os.path.join(BASE_DIR, "data", "raw"), exist_ok=True)

    enrich_media(ANIME_INPUT, ANIME_OUTPUT, "anime")
    enrich_media(MANGA_INPUT, MANGA_OUTPUT, "manga")
    # enrich_characters(CHAR_INPUT, CHAR_OUTPUT) # Désactivé par défaut (IDs instables)
