import json
import os
import sys
import logging

logger = logging.getLogger("animetix." + __name__)

# Forcer l'encodage UTF-8 pour éviter les erreurs sur Windows avec les emojis
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAW_FILE = os.path.join(BASE_DIR, 'data', 'raw', 'raw_tmdb_db.json')
CLEAN_DB = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_movies.json')
LOOKUP_FILE = os.path.join(BASE_DIR, 'data', 'artifacts', 'movie_data_for_lookup.json')

def filter_movies():
    if not os.path.exists(RAW_FILE):
        logger.error(f"❌ {RAW_FILE} not found. Run ingestion first.")
        return

    with open(RAW_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    logger.info(f"🧹 Filtering and cleaning {len(data)} items...")
    
    clean_data = []
    lookup_data = []

    for item in data:
        # Filtrage qualitatif : On veut une description et une image obligatoirement
        if not item.get('description') or len(item['description']) < 30:
            continue
        if not item.get('image'):
            continue
            
        clean_data.append(item)
        lookup_data.append({
            "id": item['id'],
            "title": item['title'],
            "title_english": item['title_english'],
            "title_native": item['title_native'],
            "image": item['image'],
            "year": item['year'],
            "type": item['media_type'], # 'Movie', 'Series' or 'Cartoon'
            "popularity": item.get('popularity', 0)
        })
    
    # Création des dossiers si manquants
    os.makedirs(os.path.dirname(CLEAN_DB), exist_ok=True)
    os.makedirs(os.path.dirname(LOOKUP_FILE), exist_ok=True)

    # Sauvegarde
    with open(CLEAN_DB, 'w', encoding='utf-8') as f:
        json.dump(clean_data, f, indent=2, ensure_ascii=False)
        
    logger.info(f"✅ Filtered down to {len(clean_data)} high-quality items.")
    logger.info(f"✅ Created {CLEAN_DB}")

if __name__ == "__main__":
    filter_movies()
