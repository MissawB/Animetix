import json
import os
import sys
import logging
import time
import httpx
from tqdm import tqdm

# Add src and backend to Python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.append(os.path.join(PROJECT_ROOT, "src"))
sys.path.append(os.path.join(PROJECT_ROOT, "src", "backend"))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')
django.setup()

from pipeline.neo4j_client import neo4j_manager
from backend.animetix.containers import get_container

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("animetix.enrichment")

# Paths
ANIME_DB = os.path.join(PROJECT_ROOT, 'data', 'processed', 'clean_root_animes.json')

def fetch_jikan_metadata(mal_id, media_type):
    """Fetches complex metadata from Jikan API: Seiyuus, Directors, exact dates."""
    metadata = {
        'entities': [],
        'relations': [],
        'exact_date': None
    }
    
    if media_type.lower() != 'anime':
        return metadata

    # 1. Fetch exact dates
    try:
        url_full = f"https://api.jikan.moe/v4/anime/{mal_id}/full"
        res = httpx.get(url_full, timeout=10, follow_redirects=True)
        if res.status_code == 200:
            data = res.json().get('data', {})
            aired = data.get('aired', {})
            metadata['exact_date'] = aired.get('string')
        time.sleep(0.5)
    except Exception as e:
        logger.warning(f"Failed to fetch dates for {mal_id}: {e}")

    # 2. Fetch Staff (Directors)
    try:
        url_staff = f"https://api.jikan.moe/v4/anime/{mal_id}/staff"
        res = httpx.get(url_staff, timeout=10, follow_redirects=True)
        if res.status_code == 200:
            staff = res.json().get('data', [])
            for s in staff:
                positions = s.get('positions', [])
                if any('Director' in p for p in positions):
                    person = s.get('person', {})
                    name = person.get('name')
                    if name:
                        metadata['entities'].append({'name': name, 'type': 'Person', 'description': 'Director'})
                        metadata['relations'].append({'source': '', 'target': name, 'type': 'DIRECTED_BY'})
        time.sleep(0.5)
    except Exception as e:
        logger.warning(f"Failed to fetch staff for {mal_id}: {e}")

    # 3. Fetch Cast (Seiyuus)
    try:
        url_chars = f"https://api.jikan.moe/v4/anime/{mal_id}/characters"
        res = httpx.get(url_chars, timeout=10, follow_redirects=True)
        if res.status_code == 200:
            chars = res.json().get('data', [])
            main_chars = [c for c in chars if c.get('role') == 'Main']
            for c in main_chars:
                voice_actors = c.get('voice_actors', [])
                jp_va = [va for va in voice_actors if va.get('language') == 'Japanese']
                for va in jp_va:
                    person = va.get('person', {})
                    name = person.get('name')
                    if name:
                        metadata['entities'].append({'name': name, 'type': 'Person', 'description': 'Seiyuu (Voice Actor)'})
                        metadata['relations'].append({'source': '', 'target': name, 'type': 'VOICED_BY'})
        time.sleep(0.5)
    except Exception as e:
        logger.warning(f"Failed to fetch cast for {mal_id}: {e}")

    return metadata

def enrich_media_type(media_type: str, limit: int = 50):
    """
    Analyzes synopses with AI and injects new entities/relations into Neo4j.
    Also fetches deep metadata from Jikan API.
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
    
    items_to_process = [it for it in data if it.get('description') and len(it['description']) > 100]
    items_to_process = items_to_process[:limit]

    logger.info(f"🕸️ Starting AI & API enrichment for {len(items_to_process)} {media_type} items...")

    for item in tqdm(items_to_process, desc=f"Enriching {media_type}"):
        try:
            title = item.get('title')
            description = item.get('description')
            media_id = str(item.get('id'))
            mal_id = str(item.get('idMal'))

            # 1. AI Extraction
            extracted = graph_service.extract_entities_and_relations(
                title=title, 
                description=description, 
                media_type=media_type
            )
            
            # 2. External API (Jikan) Extraction
            api_metadata = None
            if mal_id and mal_id != "None":
                api_metadata = fetch_jikan_metadata(mal_id, media_type)
                
                if 'entities' not in extracted:
                    extracted['entities'] = []
                if 'relations' not in extracted:
                    extracted['relations'] = []
                    
                for ent in api_metadata['entities']:
                    if not any(e['name'] == ent['name'] for e in extracted['entities']):
                        extracted['entities'].append(ent)
                        
                for rel in api_metadata['relations']:
                    rel['source'] = title
                    extracted['relations'].append(rel)

            # 3. Neo4j Injection
            if extracted.get('entities') or extracted.get('relations'):
                neo4j_manager.sync_ai_extracted_graph(media_id, extracted)
                
                if api_metadata and api_metadata.get('exact_date') and neo4j_manager.driver:
                    with neo4j_manager.driver.session() as session:
                        session.run("MATCH (m:Media {id: $id}) SET m.exact_date = $date", id=media_id, date=api_metadata['exact_date'])

                logger.debug(f"✅ Enriched {title}: {len(extracted.get('entities', []))} entities, {len(extracted.get('relations', []))} relations found.")
            else:
                logger.debug(f"ℹ️ No entities extracted for {title}.")

        except Exception as e:
            logger.error(f"❌ Error enriching {item.get('title')}: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Enrich Neo4j graph with AI and external APIs.")
    parser.add_argument("--type", type=str, default="Anime", help="Media type (Anime/Manga)")
    parser.add_argument("--limit", type=int, default=10, help="Number of items to process")
    args = parser.parse_args()

    # Ensure Django is setup since graph_builder relies on it
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')
    django.setup()

    enrich_media_type(args.type, limit=args.limit)
