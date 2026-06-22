import json
import logging
import os
import sys

from sentence_transformers import SentenceTransformer

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(BASE_DIR, "pipeline"))
from vector_client import vector_manager  # noqa: E402

logger = logging.getLogger("animetix")

CLEAN_DB = os.path.join(BASE_DIR, "data", "processed", "clean_root_actors.json")


def run_vectorization(vector_res=None):
    if not os.path.exists(CLEAN_DB):
        logger.error(f"❌ {CLEAN_DB} not found.")
        return False

    with open(CLEAN_DB, "r", encoding="utf-8") as f:
        db = json.load(f)

    # --- RÉCUPÉRATION DES IDS DÉJÀ DANS PGVECTOR ---
    manager = vector_res.manager if vector_res else vector_manager
    collection = manager.get_collection("actor_vibe")
    existing_ids = set(collection.get()["ids"])
    logger.info(f"📂 {len(existing_ids)} actors already in pgvector.")

    # --- FILTRAGE DU DELTA ET DÉDUPLICATION INTERNE ---
    new_items = []
    seen_ids_this_run = set()

    for item in db:
        item_id = str(item["id"])
        # On ignore si déjà dans pgvector OU si déjà vu dans ce fichier JSON
        if item_id not in existing_ids and item_id not in seen_ids_this_run:
            new_items.append(item)
            seen_ids_this_run.add(item_id)

    if not new_items:
        logger.info("ℹ️ Actor database is up to date.")
        return True

    logger.info(
        f"🚀 Vectorizing {len(new_items)} unique new actors (Full pgvector mode)..."
    )

    model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")

    CHUNK_SIZE = 100
    for i in range(0, len(new_items), CHUNK_SIZE):
        chunk = new_items[i : i + CHUNK_SIZE]
        logger.info(
            f"📦 Processing chunk {i // CHUNK_SIZE + 1}/{(len(new_items) - 1) // CHUNK_SIZE + 1}..."
        )

        corpus = []
        metadatas = []
        ids = []

        for item in chunk:
            ids.append(str(item["id"]))
            metadatas.append(
                {
                    "id": str(item["id"]),
                    "title": item["name"],
                    "image": item["image"] or "",
                    "popularity": item.get("popularity", 0),
                    "type": "Actor",
                }
            )

            bio = item.get("biography", "")
            roles = ", ".join(item.get("known_for", []))
            gender = item.get("gender", "")
            corpus.append(
                f"Actor Name: {item['name']}. Gender: {gender}. Known for: {roles}. Biography: {bio}"
            )

        # Calcul et injection
        embeddings = model.encode(corpus, convert_to_numpy=True)
        try:
            manager.add_to_collection("actor_vibe", ids, embeddings, metadatas)
        except Exception as e:
            logger.error(f"⚠️ Error during pgvector insertion: {e}")

    logger.info("✅ Actor pgvector Sync Complete!")
    return True
