import json
import time
import os
import sys
import logging

# Setup logging
logger = logging.getLogger("animetix." + __name__)

# Force UTF-8 for Windows output
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(BASE_DIR, "backend"))
from core.utils.security import safe_http_request

OUTPUT_FILE = os.path.join(BASE_DIR, 'data', 'raw', 'raw_anilist_db.json')

url = 'https://graphql.anilist.co'

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
    variables = {
        'page': page,
        'perPage': 50
    }
    try:
        response = safe_http_request("POST", url, json={'query': query, 'variables': variables}, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"❌ Error {response.status_code} at page {page}")
            return None
    except Exception as e:
        logger.error(f"❌ Exception at page {page}: {e}")
        return None

def run_ingestion():
    all_animes = []
    existing_ids = set()

    # Charger les données existantes si elles existent
    if os.path.exists(OUTPUT_FILE):
        logger.info(f"📂 Loading existing data from {OUTPUT_FILE}...")
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                all_animes = json.load(f)
                existing_ids = {a['id'] for a in all_animes}
            logger.info(f"✅ Found {len(all_animes)} existing animes.")
        except Exception as e:
            logger.warning(f"⚠️ Could not load existing data: {e}")

    has_next_page = True
    page = 1
    max_pages = 100 # ~5000 animes
    new_items_count = 0

    logger.info(f"🚀 Starting Anime Ingestion from AniList (Incremental)...")

    while has_next_page and page <= max_pages:
        logger.info(f"   - Fetching page {page}...")
        data = fetch_page(page)
        
        if data and 'data' in data and 'Page' in data['data']:
            page_data = data['data']['Page']
            media_list = page_data['media']
            
            added_this_page = 0
            for item in media_list:
                if item['id'] not in existing_ids:
                    all_animes.append(item)
                    existing_ids.add(item['id'])
                    new_items_count += 1
                    added_this_page += 1
            
            logger.info(f"     -> Added {added_this_page} new animes this page.")
            
            # Optionnel: si on fetch par popularité décroissante, on peut décider d'arrêter
            # si on ne trouve plus de nouveaux items sur plusieurs pages, 
            # mais ici on continue jusqu'à max_pages pour être sûr de capter les changements de popularité.
            
            has_next_page = page_data['pageInfo']['hasNextPage']
            page += 1
        else:
            logger.warning("⚠️ Stopped due to error or empty data.")
            break
        
        # AniList rate limit is 90 points per minute
        time.sleep(0.7)

    # Sauvegarde
    if new_items_count > 0:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_animes, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Collection finished! Added {new_items_count} new animes. Total: {len(all_animes)}")
    else:
        logger.info("ℹ️ No new animes found. Database is up to date.")

if __name__ == "__main__":
    run_ingestion()
