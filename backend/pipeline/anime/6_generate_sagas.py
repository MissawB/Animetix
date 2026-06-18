import os
import sys
import json
import logging
from tqdm import tqdm

# Setup logging
logger = logging.getLogger("animetix." + __name__)

# Setup environment
# abspath(__file__) is backend/pipeline/anime/6_generate_sagas.py
# 1. backend/pipeline/anime
# 2. backend/pipeline
# 3. src
# 4. root
base_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.append(os.path.join(base_dir, "src"))
sys.path.append(os.path.join(base_dir, "src", "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "animetix_project.settings")
import django  # noqa: E402
django.setup()

from backend.animetix.containers import get_container  # noqa: E402
from pipeline.neo4j_client import neo4j_manager  # noqa: E402


def run_saga_ingestion():
    logger.info("🚀 Starting Saga Ingestion & Summarization...")
    container = get_container()
    llm = container.llm_service

    # 1. Load Data
    db_path = os.path.join(base_dir, "data", "processed", "clean_root_animes.json")
    if not os.path.exists(db_path):
        logger.error(f"❌ Error: Data file not found at {db_path}")
        return

    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2. Group by Franchise
    groups = {}
    for item in data:
        # Use 'series' or 'franchise' if available, else fallback to 'title'
        # In this dataset, we'll try to group by 'series'
        franchise = item.get("series") or item.get("franchise") or item.get("title")
        if franchise not in groups:
            groups[franchise] = []
        groups[franchise].append(item)

    # Filter to only keep sagas with > 1 item for now, or all?
    # The plan says "Identify major sagas". Sagas with 1 item are just standalone titles.
    sagas = {k: v for k, v in groups.items() if len(v) > 1}
    logger.info(f"📊 Identified {len(sagas)} major sagas with multiple installments.")

    for name, items in tqdm(sagas.items(), desc="Summarizing Sagas"):
        # Collect context: take a snippet of each description to stay within context limits if needed
        # but 4000 chars is usually safe.
        full_text = "\n".join(
            [
                f"{it['title']}: {it.get('description', 'No description available')}"
                for it in items
            ]
        )

        # Generate summary
        prompt = f"Rédige un résumé exécutif dense (Lore, Thèmes, Enjeux) pour la saga '{name}' basé sur ces œuvres :\n{full_text[:4000]}"
        system = "Tu es le Chroniqueur Expert d'Animetix. Ta synthèse doit être globale et cohérente."

        try:
            summary = llm.generate(prompt, system_prompt=system)

            # Sync
            ids = [str(it["id"]) for it in items]
            neo4j_manager.sync_saga(name, summary, ids)
        except Exception as e:
            logger.warning(f"⚠️ Failed to summarize/sync saga '{name}': {e}")

    logger.info("✅ Saga ingestion complete.")


if __name__ == "__main__":
    run_saga_ingestion()
