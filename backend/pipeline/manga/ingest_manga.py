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
import sys  # noqa: E402
import time  # noqa: E402

from core.utils.security import safe_http_request  # noqa: E402

logger = logging.getLogger("animetix.pipeline." + __name__)

# Force UTF-8 for Windows output
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "raw", "raw_manga_db.json")

url = "https://graphql.anilist.co"

query = """
query ($page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    pageInfo {
      hasNextPage
    }
    media(type: MANGA, sort: POPULARITY_DESC) {
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


def run_ingestion():
    all_mangas = []
    existing_ids = set()

    # Charger les données existantes si elles existent
    if os.path.exists(OUTPUT_FILE):
        logger.info(f"📂 Loading existing data from {OUTPUT_FILE}...")
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                all_mangas = json.load(f)
                existing_ids = {a["id"] for a in all_mangas}
            logger.info(f"✅ Found {len(all_mangas)} existing mangas.")
        except Exception as e:
            logger.warning(f"⚠️ Could not load existing data: {e}")

    has_next_page = True
    page = 1
    max_pages = 100  # ~5000 mangas
    new_items_count = 0

    logger.info("🚀 Starting Manga Ingestion from AniList (Incremental)...")

    while has_next_page and page <= max_pages:
        logger.info(f"   - Fetching page {page}...")
        data = fetch_page(page)

        if data and "data" in data and "Page" in data["data"]:
            page_data = data["data"]["Page"]
            media_list = page_data["media"]

            added_this_page = 0
            for item in media_list:
                if item["id"] not in existing_ids:
                    all_mangas.append(item)
                    existing_ids.add(item["id"])
                    new_items_count += 1
                    added_this_page += 1

            logger.info(f"     -> Added {added_this_page} new mangas this page.")
            has_next_page = page_data["pageInfo"]["hasNextPage"]
            page += 1
        else:
            logger.warning("⚠️ Stopped due to error or empty data.")
            break

        time.sleep(0.7)

    # Sauvegarde
    if new_items_count > 0:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_mangas, f, indent=2, ensure_ascii=False)
        logger.info(
            f"✅ Collection finished! Added {new_items_count} new mangas. Total: {len(all_mangas)}"
        )
    else:
        logger.info("ℹ️ No new mangas found. Database is up to date.")


if __name__ == "__main__":
    run_ingestion()
