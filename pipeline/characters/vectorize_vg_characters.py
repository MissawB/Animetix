import json
import numpy as np
import os
import sys

# Force UTF-8 for Windows output
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(BASE_DIR, 'pipeline'))

from chroma_client import chroma_manager
from models_registry import models_registry

INPUT_FILE = os.path.join(BASE_DIR, 'data', 'raw', 'raw_vg_characters_db.json')
LOOKUP_FILE = os.path.join(BASE_DIR, 'data', 'artifacts', 'vg_char_data_for_lookup.json')

def run_vectorization_vg():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ {INPUT_FILE} introuvable.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        db = json.load(f)

    print(f"🚀 Vectorisation de {len(db)} personnages de Jeux Vidéo pour Similarité Cross-Media...")
    
    data_for_lookup = []
    corpus = []
    for c in db:
        data_for_lookup.append({
            "id": c['id'],
            "title": c['name'],
            "image": c['image'],
            "origin": c['origin'],
            "gender": c['gender']
        })

        # Texte riche pour l'embedding multilingue
        text = f"Video Game Character: {c['name']}. Game: {c['origin']}. Description: {c['description']}"
        corpus.append(text)

    print("Utilisation du modèle depuis ModelsRegistry...")
    model = models_registry.text_model
    
    print("✨ Encodage...")
    embeddings = model.encode(corpus, show_progress_bar=True)
    
    # --- STOCKAGE CHROMADB ---
    print("🚀 Syncing with ChromaDB (Collection: vg_character_vibe)...")
    try:
        ids = [str(c['id']) for c in data_for_lookup]
        chroma_manager.add_to_collection("vg_character_vibe", ids, embeddings, data_for_lookup)
        print("✅ ChromaDB synchronization complete.")
    except Exception as e:
        print(f"⚠️ ChromaDB Error: {e}")

    # Sauvegarde du lookup spécifique
    os.makedirs(os.path.dirname(LOOKUP_FILE), exist_ok=True)
    with open(LOOKUP_FILE, 'w', encoding='utf-8') as f:
        json.dump(data_for_lookup, f, indent=2, ensure_ascii=False)

    print(f"✅ Terminé ! {len(data_for_lookup)} personnages VG prêts pour similarité.")

if __name__ == "__main__":
    run_vectorization_vg()
