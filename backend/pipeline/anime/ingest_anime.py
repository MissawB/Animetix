import json
import logging
import os
import sys
import time

# Setup logging
logger = logging.getLogger("animetix." + __name__)

# Force UTF-8 for Windows output
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(BASE_DIR, "backend"))
from core.utils.security import safe_http_request  # noqa: E402

OUTPUT_FILE = os.path.join(BASE_DIR, "data", "raw", "raw_anilist_db.json")

url = "https://graphql.anilist.co"

query = """
query ($page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    pageInfo {
      hasNextPage
    }
    media(type: ANIME, sort: POPULARITY_DESC) {
      id
      idMal
      title {
        romaji
        english
        native
      }
      format
      description
      genres
      startDate {
        year
      }
      popularity
      source
      episodes
      studios {
        edges {
          node {
            name
            isAnimationStudio
          }
        }
      }
      coverImage {
        large
      }
      tags {
        name
        rank
      }
      relations {
        edges {
          relationType
          node {
            id
            title {
              romaji
            }
          }
        }
      }
      reviews {
        nodes {
          summary
        }
      }
      recommendations {
        nodes {
          rating
          mediaRecommendation {
            title {
              romaji
            }
          }
        }
      }
    }
  }
}
"""


def fetch_page(page):
    variables = {"page": page, "perPage": 50}
    try:
        response = safe_http_request(
            "POST", url, json={"query": query, "variables": variables}, timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"❌ Error {response.status_code} at page {page}")
            return None
    except Exception as e:
        logger.error(f"❌ Exception at page {page}: {e}")
        return None


def merge_page(all_animes, by_id, media_list):
    """Merge a fetched page into the accumulated list.

    Existing works are UPDATED in place, not skipped: a refetch is how new query
    fields (studios, source, episodes) reach works ingested before they existed.
    Returns the number of works that were genuinely new.
    """
    added = 0
    for item in media_list:
        known = by_id.get(item["id"])
        if known is None:
            all_animes.append(item)
            by_id[item["id"]] = item
            added += 1
        else:
            known.update(item)
    return added


def run_ingestion():
    # Charger les données existantes si elles existent
    all_animes = []
    by_id = {}
    if os.path.exists(OUTPUT_FILE):
        logger.info(f"📂 Loading existing data from {OUTPUT_FILE}...")
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                all_animes = json.load(f)
                by_id = {a["id"]: a for a in all_animes}
            logger.info(f"✅ Found {len(all_animes)} existing animes.")
        except Exception as e:
            logger.warning(f"⚠️ Could not load existing data: {e}")

    has_next_page = True
    page = 1
    max_pages = 100  # ~5000 animes
    new_items_count = 0

    logger.info("🚀 Starting Anime Ingestion from AniList (Incremental)...")

    while has_next_page and page <= max_pages:
        logger.info(f"   - Fetching page {page}...")
        data = fetch_page(page)

        if data and "data" in data and "Page" in data["data"]:
            page_data = data["data"]["Page"]
            media_list = page_data["media"]

            added_this_page = merge_page(all_animes, by_id, media_list)
            new_items_count += added_this_page
            logger.info(f"     -> Added {added_this_page} new animes this page.")

            # Optionnel: si on fetch par popularité décroissante, on peut décider d'arrêter
            # si on ne trouve plus de nouveaux items sur plusieurs pages,
            # mais ici on continue jusqu'à max_pages pour être sûr de capter les changements de popularité.

            has_next_page = page_data["pageInfo"]["hasNextPage"]
            page += 1
        else:
            logger.warning("⚠️ Stopped due to error or empty data.")
            break

        # AniList rate limit is 90 points per minute
        time.sleep(0.7)

    # Sauvegarde
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_animes, f, indent=2, ensure_ascii=False)
    logger.info(
        f"✅ Collection finished! Added {new_items_count} new animes. Total: {len(all_animes)}"
    )


if __name__ == "__main__":
    run_ingestion()
