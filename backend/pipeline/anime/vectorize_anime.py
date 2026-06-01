import json
import time
import os
import sys
import torch
import numpy as np
import logging
from PIL import Image
from io import BytesIO

# Setup logging
logger = logging.getLogger("animetix." + __name__)

# Force UTF-8 for Windows output
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(BASE_DIR, "backend"))
from core.utils.security import safe_http_request

INPUT_FILE = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_animes.json')

# Initialisation différée
def get_repo():
    from backend.animetix.containers import get_container
    return get_container().repository

def get_pipeline_resources():
    from pipeline.models_registry import models_registry
    from pipeline.neo4j_client import neo4j_manager
    return models_registry, neo4j_manager

BATCH_SIZE = 32

def run_vectorization(chroma_res=None, neo4j_res=None):
    """
    Pipeline de vectorisation Multimodale avec support Matryoshka (MRL).
    """
    repo = get_repo()
    models_registry, neo4j_manager = get_pipeline_resources()
    
    logger.info("🚀 Starting SOTA 2026 Multimodal Vectorization (MRL Enabled)...")
    
    if not os.path.exists(INPUT_FILE):
        logger.error(f"❌ Error: Input file {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        items = json.load(f)

    # Initialisation des modèles SOTA
    text_model = models_registry.text_model
    vision_model = models_registry.vision_model

    # On ne traite que les items non encore indexés (simulation simplifiée)
    new_items = items[:100] # On limite pour la démo

    for i in range(0, len(new_items), BATCH_SIZE):
        batch = new_items[i:i + BATCH_SIZE]
        
        # --- PHASE 1 : TEXTE (Jina-v3 avec Matryoshka) ---
        # On génère des vecteurs de dimension 1024, optimisés MRL
        descriptions = [item.get('description', '') for item in batch]
        t_embeddings = text_model.encode(descriptions, convert_to_numpy=True)
        
        # --- PHASE 2 : VISION (SigLIP) ---
        v_embeddings = []
        for item in batch:
            img_url = item.get('image')
            try:
                if img_url:
                    response = safe_http_request("GET", img_url, timeout=10)
                    img = Image.open(BytesIO(response.content)).convert('RGB')
                    v_emb = vision_model.encode(img, convert_to_numpy=True)
                    v_embeddings.append(v_emb.tolist())
                else:
                    v_embeddings.append(None)
            except Exception as e:
                logger.warning(f"Failed to fetch or encode image for {item.get('title', 'Unknown')}: {e}")
                v_embeddings.append(None)

        # --- PHASE 3 : UPSERT & SYNC ---
        for idx, item in enumerate(batch):
            ext_id = str(item['id'])
            
            # Upsert ChromaDB
            repo.upsert_items('anime_thematic', [ext_id], [t_embeddings[idx].tolist()], [item])
            if v_embeddings[idx]:
                repo.upsert_items('character_visual_vibe', [ext_id], [v_embeddings[idx]], [item])
            
            # SYNC NEO4J AUTOMATIQUE (Celery Pipeline)
            try:
                neo4j_manager.sync_media_to_graph(item, "Anime")
            except Exception as e:
                logger.warning(f"⚠️ Neo4j Sync Error for {item['title']}: {e}")

        logger.info(f"   📦 Processed {min(i + BATCH_SIZE, len(new_items))}/{len(new_items)}...")

    logger.info(f"✅ SOTA Vectorization & Neo4j Sync Complete.")
    return True

if __name__ == "__main__":
    run_vectorization()
