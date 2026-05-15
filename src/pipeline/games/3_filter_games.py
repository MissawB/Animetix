import json
import os
import sys

# Forcer l'encodage UTF-8 pour éviter les erreurs sur Windows avec les emojis
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAW_FILE = os.path.join(BASE_DIR, 'data', 'raw', 'raw_igdb_db.json')
CLEAN_DB = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_games.json')

def filter_games():
    if not os.path.exists(RAW_FILE):
        print(f"❌ {RAW_FILE} not found.")
        return

    with open(RAW_FILE, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    print(f"🧹 Filtering {len(raw_data)} games...")
    
    clean_data = []
    for game in raw_data:
        # Critères de qualité
        if not game.get('description') or len(game['description']) < 50:
            continue
        if not game.get('image'):
            continue
            
        # On garde l'ID original pour Chroma
        clean_data.append(game)

    # Sauvegarde
    os.makedirs(os.path.dirname(CLEAN_DB), exist_ok=True)
    with open(CLEAN_DB, 'w', encoding='utf-8') as f:
        json.dump(clean_data, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Filtered down to {len(clean_data)} high-quality games.")

if __name__ == "__main__":
    filter_games()
