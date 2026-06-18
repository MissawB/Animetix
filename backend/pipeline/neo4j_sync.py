import json
import logging
import os

from tqdm import tqdm

# Logger
logger = logging.getLogger("animetix." + __name__)

# Chemins des catalogues clean
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANIME_DB = os.path.join(BASE_DIR, "data", "processed", "clean_root_animes.json")
MANGA_DB = os.path.join(BASE_DIR, "data", "processed", "clean_root_mangas.json")
CHAR_DB = os.path.join(BASE_DIR, "data", "processed", "filtered_characters.json")
GAME_DB = os.path.join(BASE_DIR, "data", "processed", "clean_root_games.json")
from pipeline.neo4j_client import Neo4jManager  # noqa: E402


def run_sync_type_to_graph(media_type: str, neo4j_res=None):
    """
    Synchronise un type de média spécifique vers Neo4j.
    Utilise une ressource Neo4j si fournie, sinon le manager global.
    """
    logger.info(f"🕸️ Syncing {media_type} to Neo4j...")

    # Initialisation du manager avec la ressource si présente
    if neo4j_res:
        manager = Neo4jManager(
            uri=neo4j_res.uri, user=neo4j_res.user, password=neo4j_res.password
        )
    else:
        from pipeline.neo4j_client import neo4j_manager  # noqa: E402

        manager = neo4j_manager

    file_map = {
        "Anime": ANIME_DB,
        "Manga": MANGA_DB,
        "Character": CHAR_DB,
        "Game": GAME_DB,
    }

    db_path = file_map.get(media_type)
    if not db_path or not os.path.exists(db_path):
        logger.warning(f"⚠️ Source file for {media_type} not found.")
        return 0

    sync_count = 0
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        for item in tqdm(data, desc=f"Syncing {media_type}"):
            try:
                if media_type == "Character" and hasattr(
                    manager, "sync_character_to_graph"
                ):
                    manager.sync_character_to_graph(item)
                else:
                    manager.sync_media_to_graph(item, media_type)
                sync_count += 1
            except Exception as e:
                logger.error(
                    f"⚠️ Error syncing {media_type} {item.get('title', item.get('name'))}: {e}"
                )

    return sync_count


def run_sync_all_to_graph():
    """
    Synchronise l'intégralité du catalogue vers Neo4j.
    """
    logger.info("🕸️ Starting Global Graph Synchronization...")
    run_sync_type_to_graph("Anime")
    run_sync_type_to_graph("Manga")
    run_sync_type_to_graph("Character")
    logger.info("✅ Global Graph Sync Complete.")
    return True
