import json
import logging
import os
import sys

from sentence_transformers import SentenceTransformer

logger = logging.getLogger("animetix." + __name__)

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(BASE_DIR, "pipeline"))
from vector_client import vector_manager  # noqa: E402

logger.info("🚀 Starting Movie Vectorization (Full pgvector Mode)...")

CLEAN_DB = os.path.join(BASE_DIR, "data", "processed", "clean_root_movies.json")


def main():
    if not os.path.exists(CLEAN_DB):
        logger.error(f"❌ {CLEAN_DB} not found.")
        return

    with open(CLEAN_DB, "r", encoding="utf-8") as f:
        db = json.load(f)

    # --- RÉCUPÉRATION DES IDS DÉJÀ DANS PGVECTOR ---
    collection = vector_manager.get_collection("movie_thematic")
    existing_ids = set(collection.get()["ids"])
    logger.info(f"📂 {len(existing_ids)} movies already in pgvector.")

    # --- FILTRAGE DU DELTA & DE-DUPLICATION ---
    new_items = []
    seen_ids_in_batch = set()

    for item in db:
        item_id = str(item["id"])
        if item_id not in existing_ids and item_id not in seen_ids_in_batch:
            new_items.append(item)
            seen_ids_in_batch.add(item_id)

    if not new_items:
        logger.info("ℹ️ Movie database is up to date.")
        return

    logger.info(f"🚀 Found {len(new_items)} new movies to vectorize.")
    model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")

    CHUNK_SIZE = 100
    for i in range(0, len(new_items), CHUNK_SIZE):
        chunk = new_items[i : i + CHUNK_SIZE]
        logger.info(
            f"📦 Processing chunk {i // CHUNK_SIZE + 1}/{(len(new_items) - 1) // CHUNK_SIZE + 1}..."
        )

        thematic_corpus, plot_corpus, vibe_corpus, metadatas, ids = [], [], [], [], []

        for item in chunk:
            item_id = str(item["id"])
            ids.append(item_id)

            metadatas.append(
                {
                    "id": item_id,
                    "title": item["title"],
                    "image": item["image"] or "",
                    "year": str(item.get("year", "0000")),
                    "popularity": item.get("popularity", 0),
                    "type": item.get("media_type", "Movie"),
                }
            )

            genres = ", ".join(item.get("genres", []))
            tags = ", ".join(item.get("tags", []))
            description = item.get("description", "")
            cast = ", ".join(item.get("cast", []))
            recs = ", ".join(item.get("recommendations", {}).keys())

            thematic_corpus.append(
                f"Genres: {genres}. Keywords: {tags}. Similar to: {recs}."
            )
            plot_corpus.append(f"{description} Starring: {cast}")
            vibe_corpus.append(f"Mood: {genres}, {tags}")

        # Calcul des embeddings
        vec_thematic = model.encode(thematic_corpus, convert_to_numpy=True)
        vec_plot = model.encode(plot_corpus, convert_to_numpy=True)
        vec_vibe = model.encode(vibe_corpus, convert_to_numpy=True)

        # Injection directe dans pgvector
        try:
            vector_manager.add_to_collection(
                "movie_thematic", ids, vec_thematic, metadatas
            )
            vector_manager.add_to_collection("movie_plot", ids, vec_plot, metadatas)
            vector_manager.add_to_collection("movie_vibe", ids, vec_vibe, metadatas)
        except Exception as e:
            logger.warning(f"⚠️ pgvector sync failed for this chunk: {e}")

    logger.info("✅ Movie pgvector Sync Complete!")


if __name__ == "__main__":
    main()
