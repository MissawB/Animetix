# Fix path for internal imports
import sys
import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

import httpx
from core.utils.security import safe_http_request
import json
import time
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger("animetix.pipeline." + __name__)

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, '.env'))

OUTPUT_FILE = os.path.join(BASE_DIR, 'data', 'raw', 'raw_igdb_db.json')

# Identifiants IGDB (via Twitch Developer)
CLIENT_ID = os.getenv("IGDB_CLIENT_ID")
CLIENT_SECRET = os.getenv("IGDB_CLIENT_SECRET")

def get_twitch_token():
    """Récupère un jeton d'accès Twitch pour l'API IGDB."""
    url = f"https://id.twitch.tv/oauth2/token?client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&grant_type=client_credentials"
    try:
        response = safe_http_request("POST", url)
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            logger.error(f"❌ Error getting Twitch token: {response.text}")
    except Exception as e:
        logger.error(f"❌ Twitch Auth Exception: {e}")
    return None

def fetch_igdb(query, token):
    """Exécute une requête IGDB."""
    url = "https://api.igdb.com/v4/games"
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {token}',
        'Content-Type': 'text/plain'
    }
    try:
        response = safe_http_request("POST", url, headers=headers, content=query)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            logger.warning("⚠️ Rate limit hit, sleeping...")
            time.sleep(1)
            return fetch_igdb(query, token)
        else:
            logger.error(f"❌ IGDB Error {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"❌ IGDB Exception: {e}")
    return []

def run_ingestion():
    if not CLIENT_ID or not CLIENT_SECRET:
        logger.error("❌ Missing IGDB_CLIENT_ID or IGDB_CLIENT_SECRET in .env")
        return False

    token = get_twitch_token()
    if not token: return False

    logger.info("🎮 Collecting Popular Games from IGDB...")
    
    new_raw_data = []
    for offset in range(0, 500, 50):
        logger.info(f"   - Progress: offset {offset}...")
        query = "fields name, summary, genres.name, themes.name, platforms.name, total_rating, total_rating_count, cover.url, first_release_date, similar_games.name, storyline; sort total_rating_count desc; limit 50; offset " + str(offset) + ";"
        
        results = fetch_igdb(query, token)
        if not results: break
        
        for game in results:
            formatted = {
                "id": game['id'],
                "title": game.get('name'),
                "description": game.get('summary') or game.get('storyline') or "",
                "genres": [g['name'] for g in game.get('genres', [])],
                "themes": [t['name'] for t in game.get('themes', [])],
                "platforms": [p['name'] for p in game.get('platforms', [])],
                "rating": game.get('total_rating'),
                "year": time.strftime('%Y', time.gmtime(game['first_release_date'])) if game.get('first_release_date') else "0000",
                "image": f"https:{game['cover']['url'].replace('t_thumb', 't_cover_big')}" if game.get('cover') else None,
                "similar": [s['name'] for s in game.get('similar_games', [])[:5]]
            }
            new_raw_data.append(formatted)
        
        time.sleep(0.25)

    if not new_raw_data:
        logger.error("❌ Final attempt failed. No games retrieved.")
        return False

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_raw_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Ingestion finished! Added {len(new_raw_data)} games.")
    return True
