import json
import numpy as np
import os
import sys
import requests
from PIL import Image
from io import BytesIO

# Force UTF-8 for Windows output
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SRC_DIR = os.path.join(BASE_DIR, 'src')
BACKEND_DIR = os.path.join(SRC_DIR, 'backend')

for path in [SRC_DIR, BACKEND_DIR]:
    if path not in sys.path:
        sys.path.append(path)

# Initialisation différée
def get_repo():
    from backend.animetix.services import AnimetixService
    return AnimetixService().repository

def get_pipeline_resources():
    from pipeline.models_registry import models_registry
    from pipeline.neo4j_client import neo4j_manager
    return models_registry, neo4j_manager

CLEAN_DB = os.path.join(BASE_DIR, 'data', 'processed', 'filtered_characters.json')
BATCH_SIZE = 32

def run_vectorization():
    repo = get_repo()
    models_registry, neo4j_manager = get_pipeline_resources()
    if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    if not os.path.exists(CLEAN_DB):
        print(f"❌ {CLEAN_DB} not found."); return

    with open(CLEAN_DB, 'r', encoding='utf-8') as f:
        db = json.load(f)

    # Collections
    existing_ids = repo.get_all_ids("character_vibe")
    existing_vision_ids = repo.get_all_ids("character_visual_vibe")
    
    new_items = [item for item in db if str(item['id']) not in existing_ids or str(item['id']) not in existing_vision_ids]

    if not new_items:
        print("ℹ️ Character database up to date."); return

    print(f"🚀 Multimodal Vectorization of {len(new_items)} characters (Batching mode: {BATCH_SIZE})...")
    text_model = models_registry.text_model
    vision_model = models_registry.vision_model
    
    for i in range(0, len(new_items), BATCH_SIZE):
        batch = new_items[i:i + BATCH_SIZE]
        
        batch_ids, batch_metas, batch_texts = [], [], []
        vision_ids, vision_images, vision_metas = [], [], []

        for item in batch:
            c_id = str(item['id'])
            
            # Extraction de la popularité
            pop = item.get('popularity', 0)
            if isinstance(pop, dict):
                pop = pop.get('favourites', 0)
                
            meta = {
                "id": c_id, "title": item['name'], "image": item['image'] or "",
                "popularity": pop, "type": "Character",
                "affiliations": ", ".join(item.get('metadata', {}).get('affiliations') or [])
            }
            
            if c_id not in existing_ids:
                t_input = f"Character Vibe: {item.get('name')}. {item.get('clean_description', '')}"
                batch_ids.append(c_id)
                batch_texts.append(t_input)
                batch_metas.append(meta)

            if c_id not in existing_vision_ids and item['image']:
                try:
                    res = requests.get(item['image'], timeout=5)
                    if res.status_code == 200:
                        img = Image.open(BytesIO(res.content)).convert("RGB")
                        vision_ids.append(c_id)
                        vision_images.append(img)
                        vision_metas.append(meta)
                except Exception as e:
                    print(f"⚠️ Error fetching image for {c_id}: {e}")
                    pass
            
            try: neo4j_manager.sync_character_to_graph(item)
            except Exception as e:
                print(f"⚠️ Neo4j Sync Error for {c_id}: {e}")
                pass

        if batch_texts:
            embeddings = text_model.encode(batch_texts, convert_to_numpy=True).tolist()
            repo.upsert_items("character_vibe", batch_ids, embeddings, batch_metas)
            
        if vision_images:
            v_embeddings = vision_model.encode(vision_images, convert_to_numpy=True).tolist()
            repo.upsert_items("character_visual_vibe", vision_ids, v_embeddings, vision_metas)

        print(f"   📦 Processed {min(i + BATCH_SIZE, len(new_items))}/{len(new_items)}...")

    print(f"✅ Character Multimodal Sync Complete.")

if __name__ == "__main__":
    run_vectorization()
