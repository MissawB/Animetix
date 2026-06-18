import json
import os
import sys
import logging

# Forcer l'encodage UTF-8 pour éviter les erreurs sur Windows avec les emojis
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger("animetix")

RAW_FILE = os.path.join(BASE_DIR, "data", "raw", "raw_actors_db.json")
CLEAN_DB = os.path.join(BASE_DIR, "data", "processed", "clean_root_actors.json")
LOOKUP_FILE = os.path.join(BASE_DIR, "data", "artifacts", "actor_data_for_lookup.json")


def run_filtering():
    if not os.path.exists(RAW_FILE):
        logger.error(f"❌ {RAW_FILE} not found. Run ingestion first.")
        return False

    with open(RAW_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    logger.info(f"🧹 Filtering and cleaning {len(data)} actors...")

    clean_data = []

    for item in data:
        # On veut une biographie minimum pour la vectorisation
        if not item.get("biography") or len(item["biography"]) < 20:
            continue

        clean_data.append(item)

    # Création des dossiers si manquants
    os.makedirs(os.path.dirname(CLEAN_DB), exist_ok=True)

    # Sauvegarde
    with open(CLEAN_DB, "w", encoding="utf-8") as f:
        json.dump(clean_data, f, indent=2, ensure_ascii=False)

    logger.info(f"✅ Filtered down to {len(clean_data)} high-quality actors.")
    logger.info(f"✅ Created {CLEAN_DB}")
    return True
