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
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(BASE_DIR, 'pipeline'))

from chroma_client import chroma_manager
from neo4j_client import neo4j_manager
from models_registry import models_registry

CLEAN_DB = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_animes.json')
BATCH_SIZE = 32

def run_vectorization():
    if not os.path.exists(CLEAN_DB):
        print(f"❌ {CLEAN_DB} not found."); return

    with open(CLEAN_DB, 'r', encoding='utf-8') as f:
        db = json.load(f)

    # Collections
    existing_ids = chroma_manager.get_all_ids("anime_thematic")
    existing_vision_ids = chroma_manager.get_all_ids("anime_visual_vibe")
    existing_plot_ids = chroma_manager.get_all_ids("anime_plot")
    
    new_items = [item for item in db if str(item['id']) not in existing_ids or str(item['id']) not in existing_vision_ids or str(item['id']) not in existing_plot_ids]

    if not new_items:
        print("ℹ️ Anime database up to date."); return

    print(f"🚀 Multimodal Vectorization of {len(new_items)} animes (Batching mode: {BATCH_SIZE})...")
    
    text_model = models_registry.text_model
    vision_model = models_registry.vision_model
    
    for i in range(0, len(new_items), BATCH_SIZE):
        batch = new_items[i:i + BATCH_SIZE]
        
        batch_ids, batch_metas, batch_texts = [], [], []
        plot_ids, plot_texts, plot_metas = [], [], []
        vision_ids, vision_images, vision_metas = [], [], []

        for item in batch:
            a_id = str(item['id'])
            meta = {
                "id": a_id, "title": item['title'], "image": item['image'] or "",
                "year": str(item.get('year', "0000")), "popularity": item.get('popularity', 0), "type": "Anime",
                "genres": ", ".join(item.get('genres') or [])
            }
            
            if a_id not in existing_ids:
                t_input = f"Anime Themes: {', '.join(item.get('tags', []))}. Genres: {', '.join(item.get('genres', []))}. {item.get('description', '')}"
                batch_ids.append(a_id)
                batch_texts.append(t_input)
                batch_metas.append(meta)

            if a_id not in existing_plot_ids and item.get('description'):
                plot_ids.append(a_id)
                plot_texts.append(item['description'])
                plot_metas.append(meta)

            if a_id not in existing_vision_ids and item['image']:
                try:
                    res = requests.get(item['image'], timeout=5)
                    if res.status_code == 200:
                        img = Image.open(BytesIO(res.content)).convert("RGB")
                        vision_ids.append(a_id)
                        vision_images.append(img)
                        vision_metas.append(meta)
                except: pass
            
            try: neo4j_manager.sync_media_to_graph(item, "Anime")
            except: pass

        if batch_texts:
            embeddings = text_model.encode(batch_texts, convert_to_numpy=True)
            chroma_manager.add_to_collection("anime_thematic", batch_ids, embeddings, batch_metas)
            
        if plot_texts:
            p_embeddings = text_model.encode(plot_texts, convert_to_numpy=True)
            chroma_manager.add_to_collection("anime_plot", plot_ids, p_embeddings, plot_metas)

        if vision_images:
            v_embeddings = vision_model.encode(vision_images, convert_to_numpy=True)
            chroma_manager.add_to_collection("anime_visual_vibe", vision_ids, v_embeddings, vision_metas)

        print(f"   📦 Processed {min(i + BATCH_SIZE, len(new_items))}/{len(new_items)}...")

    print(f"✅ Anime Multimodal Sync Complete.")

if __name__ == "__main__":
    run_vectorization()
