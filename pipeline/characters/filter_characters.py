import json
import os
import sys

# Forcer l'encodage UTF-8 pour éviter les erreurs sur Windows avec les emojis
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

INPUT_FILE = os.path.join(BASE_DIR, 'data', 'processed', 'refined_characters.json')
OUTPUT_FILE = os.path.join(BASE_DIR, 'data', 'processed', 'filtered_characters.json')
LOOKUP_FILE = os.path.join(BASE_DIR, 'data', 'artifacts', 'char_data_for_lookup.json')

def run_filtering():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ {INPUT_FILE} introuvable.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        db = json.load(f)

    print(f"🧹 Filtrage de {len(db)} personnages...")
    
    # On ne garde que ceux qui ont une image et une description correcte
    filtered = []
    for c in db:
        description = c.get('clean_description') or c.get('biography') or c.get('description')
        if c.get('image') and description and len(description) > 20:
            # S'assurer que clean_description est présent pour la suite du pipeline
            if not c.get('clean_description'):
                c['clean_description'] = description
            filtered.append(c)
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(filtered, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Terminé ! {len(filtered)} personnages conservés dans {OUTPUT_FILE}.")

if __name__ == "__main__":
    run_filtering()
