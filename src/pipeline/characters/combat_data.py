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

def run_combat_data_ingestion(limit: int = 20):
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
        except Exception: pass

    # Load failed attempts registry
    failed_attempts = set()
    if os.path.exists(FAILED_ATTEMPTS_PATH):
        try:
            with open(FAILED_ATTEMPTS_PATH, 'r', encoding='utf-8') as f:
                failed_attempts = set(json.load(f))
        except Exception: pass

    container = get_container()
    vs_service: VsBattleService = container.vs_battle_service

    results = []
    count = 0
    
    for char in characters:
        name = char['name']
        
        # Skip if already processed or previously failed
        if name in existing_combat_data:
            results.append(existing_combat_data[name])
            continue
        if name in failed_attempts:
            continue
            
        if count >= limit:
            break

        try:
            logger.info(f"⚔️ Processing combat data for: {name}")
            # Add franchise if available
            franchise = char.get('franchise') or char.get('media', {}).get('title')
            combat_char = vs_service.fetch_and_parse_character(name, franchise=franchise)
            
            # Validation
            if not combat_char.summary or combat_char.summary == "No summary available.":
                logger.warning(f"⚠️ Incomplete data for {name}, marking as failed.")
                failed_attempts.add(name)
                continue
                
            results.append(combat_char.model_dump())
            count += 1
            logger.info(f"✅ Added combat data for {name}")
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
