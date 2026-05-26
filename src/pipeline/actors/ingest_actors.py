import requests
import json
import time
import os
import logging
from dotenv import load_dotenv

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, '.env'))

logger = logging.getLogger('animetix')

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
OUTPUT_FILE = os.path.join(BASE_DIR, 'data', 'raw', 'raw_actors_db.json')

if not TMDB_API_KEY:
    logger.error("❌ TMDB_API_KEY not found in .env file.")

def fetch_tmdb_page(endpoint, page=1, params={}):
    url = f"{BASE_URL}/{endpoint}"
    default_params = {"api_key": TMDB_API_KEY, "language": "fr-FR", "page": page}
    default_params.update(params)
    try:
        response = requests.get(url, params=default_params, timeout=20)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            logger.warning("⚠️ Rate limit reached. Sleeping...")
            time.sleep(10)
            return fetch_tmdb_page(endpoint, page, params)
        return None
    except: return None

def run_ingestion():
    if not TMDB_API_KEY:
        return False
        
    existing_data = []
    existing_ids = set()

    # Charger les données existantes
    if os.path.exists(OUTPUT_FILE):
        logger.info(f"📂 Loading existing data from {OUTPUT_FILE}...")
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                existing_ids = {item['id'] for item in existing_data}
            logger.info(f"✅ Found {len(existing_data)} existing actors.")
        except Exception as e:
            logger.warning(f"⚠️ Could not load existing data: {e}")

    all_raw = []
    
    logger.info("🎭 Collecting Popular Actors/Actresses from TMDB...")
    # 500 items = 25 pages
    for page in range(1, 26):
        data = fetch_tmdb_page("person/popular", page=page)
        if data: 
            for item in data.get('results', []):
                if item.get('known_for_department') == 'Acting':
                    all_raw.append(item)
        time.sleep(0.2)
    
    # On identifie les nouveaux
    new_candidates = [item for item in all_raw if item['id'] not in existing_ids]
    
    if not new_candidates:
        logger.info("ℹ️ No new actors to enrich. Database is up to date.")
        return True

    logger.info(f"✨ Enriching {len(new_candidates)} new actors (Biography, Roles)...")
    new_enriched_data = []
    for i, item in enumerate(new_candidates):
        details = fetch_tmdb_page(f"person/{item['id']}")
        
        if details:
            formatted = {
                "id": details.get('id'),
                "name": details.get('name'),
                "popularity": details.get('popularity'),
                "biography": details.get('biography'),
                "image": f"https://image.tmdb.org/t/p/w500{details.get('profile_path')}" if details.get('profile_path') else None,
                "gender": "Female" if details.get('gender') == 1 else "Male",
                "known_for": [m.get('title') or m.get('name') for m in item.get('known_for', [])]
            }
            new_enriched_data.append(formatted)
        
        if (i+1) % 20 == 0:
            logger.info(f"📦 Enriched {i+1}/{len(new_candidates)}...")
        time.sleep(0.1)

    # Fusion
    final_data = existing_data + new_enriched_data

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Actor collection finished! Added {len(new_enriched_data)} new actors. Total: {len(final_data)}")
    return True
