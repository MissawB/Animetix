import json
import os
import sys

# Forcer l'encodage UTF-8 pour éviter les erreurs sur Windows avec les emojis
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAW_FILE = os.path.join(BASE_DIR, 'data', 'raw', 'raw_actors_db.json')
CLEAN_DB = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_actors.json')
LOOKUP_FILE = os.path.join(BASE_DIR, 'data', 'artifacts', 'actor_data_for_lookup.json')

def filter_actors():
    if not os.path.exists(RAW_FILE):
        print(f"❌ {RAW_FILE} not found. Run ingestion first.")
        return

    with open(RAW_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"🧹 Filtering and cleaning {len(data)} actors...")
    
    clean_data = []
    lookup_data = []

    for item in data:
        # On veut une biographie minimum pour la vectorisation
        if not item.get('biography') or len(item['biography']) < 20:
            continue
            
        clean_data.append(item)
    
    # Création des dossiers si manquants
    os.makedirs(os.path.dirname(CLEAN_DB), exist_ok=True)

    # Sauvegarde
    with open(CLEAN_DB, 'w', encoding='utf-8') as f:
        json.dump(clean_data, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Filtered down to {len(clean_data)} high-quality actors.")
    print(f"✅ Created {CLEAN_DB}")

if __name__ == "__main__":
    filter_actors()
