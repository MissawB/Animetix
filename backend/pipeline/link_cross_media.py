import json
import logging
import os

from pipeline.neo4j_client import neo4j_manager
from tqdm import tqdm

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("animetix.cross_media")

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
ANIME_DB = os.path.join(PROJECT_ROOT, "data", "processed", "clean_root_animes.json")
MANGA_DB = os.path.join(PROJECT_ROOT, "data", "processed", "clean_root_mangas.json")


def run_cross_media_linking():
    """
    Links Animes to their source Mangas in Neo4j based on MAL IDs or Title matches.
    """
    logger.info("🕸️ Starting Cross-Media Linking (Anime <-> Manga)...")

    if not os.path.exists(ANIME_DB) or not os.path.exists(MANGA_DB):
        logger.error("Source databases not found.")
        return

    with open(ANIME_DB, "r", encoding="utf-8") as f:
        animes = json.load(f)
    with open(MANGA_DB, "r", encoding="utf-8") as f:
        mangas = json.load(f)

    # Index mangas by idMal and Title for fast lookup
    manga_by_mal = {str(m.get("idMal")): str(m["id"]) for m in mangas if m.get("idMal")}
    manga_by_title = {
        m["title"].lower(): str(m["id"]) for m in mangas if m.get("title")
    }

    links_found = 0

    # We iterate over animes to find their manga counterpart
    for anime in tqdm(animes, desc="Linking Animes"):
        anime_id = str(anime["id"])
        mal_id = str(anime.get("idMal"))
        title = anime["title"].lower()

        target_manga_id = None

        # 1. Match by MAL ID
        if mal_id in manga_by_mal:
            target_manga_id = manga_by_mal[mal_id]

        # 2. Match by exact Title (if no MAL match)
        elif title in manga_by_title:
            target_manga_id = manga_by_title[title]

        if target_manga_id:
            # Inject relation into Neo4j
            if neo4j_manager.driver:
                with neo4j_manager.driver.session() as session:
                    query = """
                    MATCH (a:Media {id: $a_id, type: 'Anime'})
                    MATCH (m:Media {id: $m_id, type: 'Manga'})
                    MERGE (a)-[r:ADAPTED_FROM]->(m)
                    RETURN r
                    """
                    session.run(query, a_id=anime_id, m_id=target_manga_id)
            links_found += 1

    logger.info(
        f"✅ Linking Complete. {links_found} relations established between Anime and Manga."
    )


if __name__ == "__main__":
    run_cross_media_linking()
