import json
from sentence_transformers import SentenceTransformer
import numpy as np
import os
import sys
import logging

logger = logging.getLogger("animetix.pipeline." + __name__)

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(
    os.path.dirname(BASE_DIR)
)  # Pour importer chroma_client si besoin (ou ajuster selon structure)
# Plus simple:
sys.path.append(os.path.join(BASE_DIR, "pipeline"))
from chroma_client import chroma_manager  # noqa: E402

CLEAN_DB = os.path.join(BASE_DIR, "data", "processed", "clean_root_games.json")
LOOKUP_FILE = os.path.join(BASE_DIR, "data", "artifacts", "game_data_for_lookup.json")
VEC_THEMATIC = os.path.join(BASE_DIR, "data", "artifacts", "game_thematic_vectors.npy")
VEC_PLOT = os.path.join(BASE_DIR, "data", "artifacts", "game_plot_vectors.npy")
VEC_VIBE = os.path.join(BASE_DIR, "data", "artifacts", "game_vibe_vectors.npy")


def run_vectorization(chroma_res=None):
    if not os.path.exists(CLEAN_DB):
        logger.error(f"❌ {CLEAN_DB} not found.")
        return False

    with open(CLEAN_DB, "r", encoding="utf-8") as f:
        db = json.load(f)

    # --- CHARGEMENT DES DONNÉES EXISTANTES ---
    existing_lookup = []
    existing_ids = set()
    old_thematic = None
    old_plot = None
    old_vibe = None

    if os.path.exists(LOOKUP_FILE):
        logger.info("📂 Loading existing lookup and vectors...")
        try:
            with open(LOOKUP_FILE, "r", encoding="utf-8") as f:
                existing_lookup = json.load(f)
                existing_ids = {
                    item.get("id") for item in existing_lookup if item.get("id")
                }

            if os.path.exists(VEC_THEMATIC):
                old_thematic = np.load(VEC_THEMATIC)
                old_plot = np.load(VEC_PLOT)
                old_vibe = np.load(VEC_VIBE)
                logger.info(f"✅ Loaded {len(existing_ids)} existing vectors.")
        except Exception as e:
            logger.warning(f"⚠️ Error loading existing artifacts: {e}")

    # --- FILTRAGE DU DELTA ---
    new_items = [item for item in db if item["id"] not in existing_ids]

    if not new_items:
        logger.info("ℹ️ No new games to vectorize. Everything is up to date.")
        return True

    logger.info(f"🚀 Found {len(new_items)} new games to vectorize.")

    # --- Data Preparation ---
    new_data_for_lookup = []
    thematic_corpus = []
    plot_corpus = []
    vibe_corpus = []

    for item in new_items:
        new_data_for_lookup.append(
            {
                "id": item["id"],
                "title": item["title"],
                "image": item["image"],
                "year": item["year"],
                "popularity": item.get("rating", 0),
            }
        )

        genres = ", ".join(item.get("genres", []))
        themes = ", ".join(item.get("themes", []))
        platforms = ", ".join(item.get("platforms", []))
        description = item.get("description", "")
        similar = ", ".join(item.get("similar", []))

        thematic_corpus.append(
            f"Genres: {genres}. Themes: {themes}. Platforms: {platforms}. Similar to: {similar}."
        )
        plot_corpus.append(description)
        vibe_corpus.append(f"Mood: {genres}, {themes}")

    # --- Calculating Embeddings ---
    logger.info("Loading model (paraphrase-multilingual-mpnet-base-v2)...")
    model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")

    logger.info(f"✨ Encoding {len(new_items)} vectors...")
    new_thematic = model.encode(thematic_corpus, show_progress_bar=True)
    new_plot = model.encode(plot_corpus, show_progress_bar=True)
    new_vibe = model.encode(vibe_corpus, show_progress_bar=True)

    # --- STOCKAGE CHROMADB ---
    logger.info("🚀 Syncing with ChromaDB...")
    try:
        ids = [str(item["id"]) for item in new_data_for_lookup]
        metadatas = new_data_for_lookup

        manager = chroma_res.manager if chroma_res else chroma_manager
        manager.add_to_collection("game_thematic", ids, new_thematic, metadatas)
        manager.add_to_collection("game_plot", ids, new_plot, metadatas)
        manager.add_to_collection("game_vibe", ids, new_vibe, metadatas)
        logger.info("✅ ChromaDB synchronization complete.")
    except Exception as e:
        logger.warning(f"⚠️ ChromaDB Error: {e}")

    # --- Fusion et Sauvegarde Backup ---
    logger.info("Merging and saving artifacts...")
    if old_thematic is not None and len(old_thematic) > 0:
        final_thematic = np.concatenate([old_thematic, new_thematic])
        final_plot = np.concatenate([old_plot, new_plot])
        final_vibe = np.concatenate([old_vibe, new_vibe])
        final_lookup = existing_lookup + new_data_for_lookup
    else:
        final_thematic = new_thematic
        final_plot = new_plot
        final_vibe = new_vibe
        final_lookup = new_data_for_lookup

    os.makedirs(os.path.dirname(VEC_THEMATIC), exist_ok=True)
    np.save(VEC_THEMATIC, final_thematic)
    np.save(VEC_PLOT, final_plot)
    np.save(VEC_VIBE, final_vibe)

    with open(LOOKUP_FILE, "w", encoding="utf-8") as f:
        json.dump(final_lookup, f, indent=2, ensure_ascii=False)

    logger.info(
        f"✅ Incremental Game Vectorization Complete! Total: {len(final_lookup)}"
    )
    return True
