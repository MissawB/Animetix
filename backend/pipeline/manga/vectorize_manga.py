import json
import numpy as np
import os
import sys
import httpx
import logging
from PIL import Image
from io import BytesIO

# Force UTF-8 for Windows output
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logger = logging.getLogger("animetix.pipeline." + __name__)

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(BASE_DIR, 'pipeline'))

# Initialisation différée
def get_repo():
    from backend.animetix.containers import get_container
    return get_container().repository

def get_pipeline_resources():
    from pipeline.models_registry import models_registry
    from pipeline.neo4j_client import neo4j_manager
    return models_registry, neo4j_manager

CLEAN_DB = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_mangas.json')
BATCH_SIZE = 32 # Taille optimale pour l'inférence sans GPU

def run_vectorization():
    repo = get_repo()
    models_registry, neo4j_manager = get_pipeline_resources()
    try:
        if not os.path.exists(CLEAN_DB):
            logger.error(f"❌ {CLEAN_DB} not found."); return

        with open(CLEAN_DB, 'r', encoding='utf-8') as f:
            db = json.load(f)

        # Collections
        existing_ids = repo.get_all_ids("manga_thematic")
        existing_vision_ids = repo.get_all_ids("manga_visual_vibe")
        existing_plot_ids = repo.get_all_ids("manga_plot")
        
        new_items = [item for item in db if str(item['id']) not in existing_ids or str(item['id']) not in existing_vision_ids or str(item['id']) not in existing_plot_ids]

        if not new_items:
            logger.info("ℹ️ Manga database up to date."); return

        logger.info(f"🚀 Multimodal Vectorization of {len(new_items)} mangas (Batching mode: {BATCH_SIZE})...")
        
        text_model = models_registry.text_model
        vision_model = models_registry.vision_model
        
        # Traitement par lots (Batches)
        for i in range(0, len(new_items), BATCH_SIZE):
            batch = new_items[i:i + BATCH_SIZE]
            
            batch_ids, batch_metas, batch_texts = [], [], []
            plot_ids, plot_texts, plot_metas = [], [], []
            vision_ids, vision_images, vision_metas = [], [], []

            for item in batch:
                m_id = str(item['id'])
                meta = {
                    "id": m_id, "title": item['title'], "image": item['image'] or "",
                    "year": str(item.get('year', "0000")), "popularity": item.get('popularity', 0), "type": "Manga",
                    "genres": ", ".join(item.get('genres') or [])
                }
                
                # Préparation Text
                if m_id not in existing_ids:
                    t_input = f"Manga Themes: {', '.join(item.get('tags', []))}. Genres: {', '.join(item.get('genres', []))}. {item.get('description', '')}"
                    batch_ids.append(m_id)
                    batch_texts.append(t_input)
                    batch_metas.append(meta)

                # Préparation Plot
                if m_id not in existing_plot_ids and item.get('description'):
                    plot_ids.append(m_id)
                    plot_texts.append(item['description'])
                    plot_metas.append(meta)

                # Préparation Vision
                if m_id not in existing_vision_ids and item['image']:
                    try:
                        res = httpx.get(item['image'], timeout=2, follow_redirects=True)
 
                        if res.status_code == 200:
                            img = Image.open(BytesIO(res.content)).convert("RGB")
                            vision_ids.append(m_id)
                            vision_images.append(img)
                            vision_metas.append(meta)
                    except Exception as e:
                        logger.warning(f"⚠️ Error fetching image for {m_id}: {e}")
                        pass

                    try: neo4j_manager.sync_media_to_graph(item, "Manga")
                    except Exception as e:
                        logger.warning(f"⚠️ Neo4j Sync Error for {m_id}: {e}")
                        pass

            # Exécution des Inférences
            if batch_texts:
                embeddings = text_model.encode(batch_texts, convert_to_numpy=True).tolist()
                repo.upsert_items("manga_thematic", batch_ids, embeddings, batch_metas)
            
            if plot_texts:
                p_embeddings = text_model.encode(plot_texts, convert_to_numpy=True).tolist()
                repo.upsert_items("manga_plot", plot_ids, p_embeddings, plot_metas)
                
            if vision_images:
                v_embeddings = vision_model.encode(vision_images, convert_to_numpy=True).tolist()
                repo.upsert_items("manga_visual_vibe", vision_ids, v_embeddings, vision_metas)

            logger.info(f"   📦 Processed {min(i + BATCH_SIZE, len(new_items))}/{len(new_items)}...")

        logger.info(f"✅ Manga Multimodal Sync Complete.")

    except Exception as e:
        import traceback
        error_msg = f"CRITICAL ERROR in run_vectorization():\n{e}\n{traceback.format_exc()}"
        logger.error(error_msg)
        with open(os.path.join(BASE_DIR, "manga_vectorize_error.log"), "a", encoding="utf-8") as f:
            f.write(error_msg + "\n")

if __name__ == "__main__":
    run_vectorization()
  run_vectorization()
