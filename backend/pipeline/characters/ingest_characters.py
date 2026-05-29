import httpx
import json
import time
import os
import sys
import logging

# Logger
logger = logging.getLogger("animetix." + __name__)

# Force UTF-8 for Windows output
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILE_PATH = os.path.join(BASE_DIR, 'data', 'raw', 'raw_characters_db.json')

url = 'https://graphql.anilist.co'

query = """
query ($page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    pageInfo {
      hasNextPage
    }
    characters(sort: FAVOURITES_DESC) {
      id
      name {
        full
        native
        alternative
      }
      image {
        large
      }
      description
      gender
      age
      media(sort: POPULARITY_DESC, perPage: 1) {
        nodes {
          id
          title {
            romaji
            english
          }
        }
      }
    }
  }
}
"""

def fetch_page(page, retries=3):
    variables = {'page': page, 'perPage': 50}
    for i in range(retries):
        try:
            response = httpx.post(url, json={'query': query, 'variables': variables}, timeout=30, follow_redirects=True)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                wait_time = (i + 1) * 30 # Attente progressive : 30s, 60s, 90s
                logger.warning(f"⚠️ Erreur 429 (Rate Limit). Attente de {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"❌ Erreur {response.status_code} à la page {page}")
                return None
        except Exception as e:
            logger.error(f"❌ Exception à la page {page}: {e}")
            time.sleep(5)
    return None

def run_ingestion():
    existing_characters = []
    existing_ids = set()
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            existing_characters = json.load(f)
            existing_ids = {c['id'] for c in existing_characters}

    new_added_count = 0
    has_next_page = True
    page = 1
    max_pages = 60

    logger.info(f"🚀 Ingestion des personnages (Déjà connus: {len(existing_characters)})...")

    while has_next_page and page <= max_pages:
        logger.info(f"   - Page {page}...")
        data = fetch_page(page)
        
        if data and 'data' in data and 'Page' in data['data']:
            page_data = data['data']['Page']
            for char in page_data['characters']:
                if char['id'] not in existing_ids:
                    origin_media = char['media']['nodes'][0]['title']['romaji'] if char['media']['nodes'] else "Inconnu"
                    char_flat = {
                        "id": char['id'],
                        "name": char['name']['full'],
                        "name_native": char['name']['native'],
                        "image": char['image']['large'],
                        "description": char['description'],
                        "origin": origin_media,
                        "gender": char['gender'],
                        "age": char['age']
                    }
                    existing_characters.append(char_flat)
                    existing_ids.add(char['id'])
                    new_added_count += 1
            has_next_page = page_data['pageInfo']['hasNextPage']
            page += 1
            time.sleep(1) # Pause entre les pages pour respecter les limites
        else:
            logger.error(f"🛑 Arrêt à la page {page} due à une erreur persistante.")
            break

    if new_added_count > 0:
        os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(existing_characters, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Terminé ! {new_added_count} nouveaux personnages ajoutés (Total: {len(existing_characters)}).")
    else:
        logger.info("✅ Terminé ! Aucun nouveau personnage à ajouter.")

if __name__ == "__main__":
    run_ingestion()
