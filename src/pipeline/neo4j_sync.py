import json
import os
from tqdm import tqdm
from pipeline.neo4j_client import neo4j_manager

# Chemins des catalogues clean
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANIME_DB = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_animes.json')
MANGA_DB = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_mangas.json')
CHAR_DB = os.path.join(BASE_DIR, 'data', 'processed', 'filtered_characters.json')

def run_sync_type_to_graph(media_type: str):
    """
    Synchronise un type de média spécifique vers Neo4j.
    """
    print(f"🕸️ Syncing {media_type} to Neo4j...")
    
    file_map = {
        "Anime": ANIME_DB,
        "Manga": MANGA_DB,
        "Character": CHAR_DB
    }
    
    db_path = file_map.get(media_type)
    if not db_path or not os.path.exists(db_path):
        print(f"⚠️ Source file for {media_type} not found.")
        return False

    with open(db_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in tqdm(data, desc=f"Syncing {media_type}"):
            try:
                if media_type == "Character" and hasattr(neo4j_manager, 'sync_character_to_graph'):
                    neo4j_manager.sync_character_to_graph(item)
                else:
                    neo4j_manager.sync_media_to_graph(item, media_type)
            except Exception as e:
                print(f"⚠️ Error syncing {media_type} {item.get('title', item.get('name'))}: {e}")
                
    return True

def run_sync_all_to_graph():
    """
    Synchronise l'intégralité du catalogue vers Neo4j.
    """
    print("🕸️ Starting Global Graph Synchronization...")
    run_sync_type_to_graph("Anime")
    run_sync_type_to_graph("Manga")
    run_sync_type_to_graph("Character")
    print("✅ Global Graph Sync Complete.")
    return True
