import json
import os
import logging
from typing import List, Dict, Any
from src.core.domain.entities.ai_schemas import CombatCharacter
from src.core.domain.services.creative.vs_battle_service import VsBattleService
from src.backend.animetix.containers import get_container

logger = logging.getLogger("animetix.pipeline.combat")

# Project paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FILTERED_CHARS_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'filtered_characters.json')
COMBAT_DATA_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'combat_data.json')
FAILED_ATTEMPTS_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'failed_attempts.json')

def run_combat_data_ingestion(limit: int = 100):
    """
    Enriches filtered characters with combat data from VS Battles Wiki,
    maintaining a registry of failed attempts to skip them in future runs.
    """
    if not os.path.exists(FILTERED_CHARS_PATH):
        logger.error(f"❌ {FILTERED_CHARS_PATH} not found.")
        return False

    with open(FILTERED_CHARS_PATH, 'r', encoding='utf-8') as f:
        characters = json.load(f)

    # Load existing combat data
    existing_combat_data = {}
    if os.path.exists(COMBAT_DATA_PATH):
        try:
            with open(COMBAT_DATA_PATH, 'r', encoding='utf-8') as f:
                data_list = json.load(f)
                existing_combat_data = {c['name']: c for c in data_list}
        except Exception as e:
            logger.error("Error loading combat data from %s: %s", COMBAT_DATA_PATH, e, exc_info=True)

    # Load failed attempts registry
    failed_attempts = set()
    if os.path.exists(FAILED_ATTEMPTS_PATH):
        try:
            with open(FAILED_ATTEMPTS_PATH, 'r', encoding='utf-8') as f:
                failed_attempts = set(json.load(f))
        except Exception as e:
            logger.error("Error loading failed attempts from %s: %s", FAILED_ATTEMPTS_PATH, e, exc_info=True)

    container = get_container()
    vs_service: VsBattleService = container.vs_battle_service()

    results = []
    count = 0
    
    seen_version_urls = set()
    for char in characters:
        name = char['name']
        
        # Skip if already processed or previously failed
        if name in existing_combat_data:
            results.append(existing_combat_data[name])
            # Add existing URLs to seen set to avoid duplicates when adding new ones
            seen_version_urls.add(existing_combat_data[name].get('wiki_url'))
            continue
        if name in failed_attempts:
            continue
            
        if count >= limit:
            break

        try:
            logger.info(f"⚔️ Processing combat data for: {name}")
            # Add franchise if available
            franchise = char.get('franchise') or char.get('media', {}).get('title')
            
            # Fetch ALL versions of the character
            combat_versions = vs_service.fetch_character_versions(name, franchise=franchise)
            
            if not combat_versions:
                logger.warning(f"⚠️ No valid profiles found for {name}, marking as failed.")
                failed_attempts.add(name)
                continue
                
            for combat_char in combat_versions:
                # Validation: if summary is missing, skip this specific version
                if not combat_char.summary or combat_char.summary == "No summary available.":
                    continue
                
                # Deduplication by URL
                if combat_char.wiki_url in seen_version_urls:
                    logger.info(f"⏩ Skipping duplicate version: {combat_char.name}")
                    continue
                
                results.append(combat_char.model_dump())
                seen_version_urls.add(combat_char.wiki_url)
                logger.info(f"✅ Added version: {combat_char.name}")
            
            count += 1 
        except Exception as e:
            logger.error(f"❌ Failed to process {name}: {e}")
            failed_attempts.add(name)
            continue

    # Save enriched data
    os.makedirs(os.path.dirname(COMBAT_DATA_PATH), exist_ok=True)
    with open(COMBAT_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    # Save failed attempts registry
    with open(FAILED_ATTEMPTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(list(failed_attempts), f, indent=2)

    logger.info(f"🎯 Combat data ingestion complete. Total: {len(results)}, Failed: {len(failed_attempts)}")
    return True
