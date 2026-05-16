import json
import os
import logging
from tqdm import tqdm
from pipeline.neo4j_client import neo4j_manager
from src.backend.animetix.containers import get_container

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("animetix.enrichment")

# Paths
# This assumes the script is in src/pipeline/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
ANIME_DB = os.path.join(PROJECT_ROOT, 'data', 'processed', 'clean_root_animes.json')


def enrich_media_type(media_type: str, limit: int = 50):
    """
    Analyzes synopses with AI and injects new entities/relations into Neo4j.
    Limited by default to avoid excessive LLM costs during dev/test.
    """
    container = get_container()
    graph_service = container.graph_builder
    
    file_map = {
        "Anime": ANIME_DB,
    }
    
    db_path = file_map.get(media_type)
    if not db_path or not os.path.exists(db_path):
        logger.error(f"Source file for {media_type} not found at {db_path}")
        return

    with open(db_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Selection of items (prioritize those with long descriptions)
    items_to_process = [it for it in data if it.get('description') and len(it['description']) > 100]
    items_to_process = items_to_process[:limit]

    logger.info(f"🕸️ Starting AI enrichment for {len(items_to_process)} {media_type} items...")

    for item in tqdm(items_to_process, desc=f"Enriching {media_type}"):
        try:
            title = item.get('title')
            description = item.get('description')
            media_id = str(item.get('id'))

            # 1. AI Extraction
            extracted = graph_service.extract_entities_and_relations(
                title=title, 
                description=description, 
                media_type=media_type
            )

            # 2. Neo4j Injection
            if extracted.get('entities') or extracted.get('relations'):
                neo4j_manager.sync_ai_extracted_graph(media_id, extracted)
                logger.debug(f"✅ Enriched {title}: {len(extracted.get('entities', []))} entities found.")
            else:
                logger.debug(f"ℹ️ No entities extracted for {title}.")

        except Exception as e:
            logger.error(f"❌ Error enriching {item.get('title')}: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Enrich Neo4j graph with AI-extracted data.")
    parser.add_argument("--type", type=str, default="Anime", help="Media type (Anime/Manga)")
    parser.add_argument("--limit", type=int, default=10, help="Number of items to process")
    args = parser.parse_args()

    enrich_media_type(args.type, limit=args.limit)
