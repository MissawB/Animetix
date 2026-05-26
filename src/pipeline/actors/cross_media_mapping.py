import json
import os
import sys
import logging

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(BASE_DIR, 'pipeline'))
from chroma_client import chroma_manager

logger = logging.getLogger('animetix')

logger.info("🔗 Starting Cross-Media Mapping (Characters <-> Actors) via ChromaDB...")

# Fichier de sortie
MAP_CHAR_ACTOR = os.path.join(BASE_DIR, 'data', 'artifacts', 'char_to_actor_map.json')

def run_mapping(chroma_res=None):
    logger.info(f"   - Mapping character_vibe to actor_vibe...")
    
    manager = chroma_res.manager if chroma_res else chroma_manager
    try:
        source_coll = manager.get_collection("character_vibe")
        target_coll = manager.get_collection("actor_vibe")
    except Exception as e:
        logger.error(f"⚠️ Collection error: {e}")
        return False

    source_data = source_coll.get(include=['embeddings', 'metadatas'])
    if not source_data['ids']:
        logger.warning(f"⚠️ Character collection is empty.")
        return True

    mapping = {}
    ids = source_data['ids']
    embeddings = source_data['embeddings']
    metadatas = source_data['metadatas']

    logger.info(f"   - Processing {len(ids)} characters...")

    BATCH_SIZE = 50
    for i in range(0, len(ids), BATCH_SIZE):
        batch_end = i + BATCH_SIZE
        batch_ids = ids[i:batch_end]
        batch_embeddings = embeddings[i:batch_end]
        batch_meta = metadatas[i:batch_end]

        # Recherche des acteurs les plus proches
        results = target_coll.query(
            query_embeddings=batch_embeddings,
            n_results=1
        )

        for j, char_id in enumerate(batch_ids):
            char_name = batch_meta[j].get('title') # 'title' est le nom du perso dans les metadata Chroma
            
            if results['metadatas'][j]:
                actor_meta = results['metadatas'][j][0]
                dist = results['distances'][j][0]
                
                mapping[char_name] = {
                    "actor_name": actor_meta.get('title'),
                    "actor_image": actor_meta.get('image'),
                    "similarity": round((1 - dist) * 100, 2)
                }

    os.makedirs(os.path.dirname(MAP_CHAR_ACTOR), exist_ok=True)
    with open(MAP_CHAR_ACTOR, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)
    logger.info(f"✅ Character-Actor Mapping saved to {MAP_CHAR_ACTOR}")
    return True
