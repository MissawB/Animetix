import requests
import json
import os
import time
from typing import List, Dict

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DRIFT_REPORT = os.path.join(BASE_DIR, 'data', 'mlops', 'drift_report_latest.json')
RAW_DB = os.path.join(BASE_DIR, 'data', 'raw', 'raw_anilist_db.json')
ANILIST_URL = 'https://graphql.anilist.co'

QUERY_BY_MAL_ID = """
query ($idMal: Int) {
  Media(idMal: $idMal, type: ANIME) {
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
"""

def fetch_by_mal_id(mal_id: int):
    variables = {'idMal': mal_id}
    try:
        response = requests.post(ANILIST_URL, json={'query': QUERY_BY_MAL_ID, 'variables': variables}, timeout=30)
        if response.status_code == 200:
            return response.json().get('data', {}).get('Media')
        else:
            print(f"❌ Error {response.status_code} for MAL ID {mal_id}")
            return None
    except Exception as e:
        print(f"❌ Exception for MAL ID {mal_id}: {e}")
        return None

def run_reconciliation():
    if not os.path.exists(DRIFT_REPORT):
        print("ℹ️ No drift report found. Skipping reconciliation.")
        return False

    with open(DRIFT_REPORT, 'r', encoding='utf-8') as f:
        report = json.load(f)

    if not report.get('needs_refresh') and not report.get('missing_items'):
        print("✅ Data is up to date according to report.")
        return False

    missing_items = report.get('missing_items', [])
    if not missing_items:
        print("ℹ️ No specific missing items listed.")
        return False

    print(f"🔄 Reconciling {len(missing_items)} missing items from drift report...")

    # Load existing raw DB
    if os.path.exists(RAW_DB):
        with open(RAW_DB, 'r', encoding='utf-8') as f:
            all_animes = json.load(f)
            existing_ids = {a['id'] for a in all_animes}
    else:
        all_animes = []
        existing_ids = set()

    added_count = 0
    for item in missing_items:
        mal_id = int(item['id'])
        print(f"   - Fetching MAL ID {mal_id} ({item['title']})...")
        anime_data = fetch_by_mal_id(mal_id)
        
        if anime_data and anime_data['id'] not in existing_ids:
            all_animes.append(anime_data)
            existing_ids.add(anime_data['id'])
            added_count += 1
            print(f"     ✅ Added: {anime_data['title']['romaji']}")
        
        time.sleep(0.7) # AniList rate limit

    if added_count > 0:
        with open(RAW_DB, 'w', encoding='utf-8') as f:
            json.dump(all_animes, f, indent=2, ensure_ascii=False)
        print(f"🚀 Reconciliation complete! Added {added_count} items.")
        return True
    
    print("ℹ️ No new items were actually added.")
    return False

if __name__ == "__main__":
    run_reconciliation()
