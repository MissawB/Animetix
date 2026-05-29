import httpx
import json
import time
import os
import logging
from dotenv import load_dotenv

# Logger configuration
logger = logging.getLogger("animetix." + __name__)

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, '.env'))

OUTPUT_FILE = os.path.join(BASE_DIR, 'data', 'raw', 'raw_vg_characters_db.json')

# Identifiants IGDB
CLIENT_ID = os.getenv("IGDB_CLIENT_ID")
CLIENT_SECRET = os.getenv("IGDB_CLIENT_SECRET")

def get_twitch_token():
    url = f"https://id.twitch.tv/oauth2/token?client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&grant_type=client_credentials"
    try:
        res = httpx.post(url, follow_redirects=True)
        return res.json().get('access_token') if res.status_code == 200 else None
    except Exception as e:
        logger.error(f"Failed to acquire Twitch token: {e}")
        return None

def fetch_igdb_characters(token):
    url = "https://api.igdb.com/v4/characters"
    headers = {'Client-ID': CLIENT_ID, 'Authorization': f'Bearer {token}'}
    
    # On récupère les personnages célèbres (ceux qui ont une image et une description longue)
    # On trie par 'id' car IGDB n'a pas de score de popularité direct sur les personnages, 
    # mais on peut filtrer par les jeux auxquels ils appartiennent.
    query = """
    fields name, description, mug_shot.url, gender, games.name;
    where description != null & mug_shot != null;
    limit 250;
    sort id desc;
    """
    
    try:
        response = httpx.post(url, headers=headers, content=query, follow_redirects=True)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"❌ IGDB Character Error: {e}")
    return []

def run_ingestion_vg():
    if not CLIENT_ID or not CLIENT_SECRET:
        logger.error("❌ Missing IGDB credentials")
        return

    token = get_twitch_token()
    if not token: return

    logger.info("🎮 Collecting Famous Video Game Characters...")
    characters = fetch_igdb_characters(token)
    
    formatted_chars = []
    for c in characters:
        # Standardisation au format 'Character' du projet
        formatted = {
            "id": f"vg_{c['id']}",
            "name": c['name'],
            "description": c.get('description'),
            "image": f"https:{c['mug_shot']['url'].replace('t_thumb', 't_cover_big')}" if c.get('mug_shot') else None,
            "gender": "Male" if c.get('gender') == 1 else "Female" if c.get('gender') == 2 else "Other",
            "origin": c['games'][0]['name'] if c.get('games') else "Video Game",
            "metadata": {
                "source": "IGDB",
                "game_list": [g['name'] for g in c.get('games', [])]
            }
        }
        formatted_chars.append(formatted)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(formatted_chars, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Saved {len(formatted_chars)} Video Game characters to {OUTPUT_FILE}")

if __name__ == "__main__":
    run_ingestion_vg()
