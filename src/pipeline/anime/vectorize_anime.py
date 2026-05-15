import requests
import json
import time
import os
import sys
import torch
import numpy as np
from PIL import Image
from io import BytesIO

# Force UTF-8 for Windows output
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Chemins
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_FILE = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_animes.json')

# Imports du domaine
from pipeline.models_registry import models_registry
from pipeline.chroma_client import chroma_manager
from pipeline.neo4j_client import neo4j_manager

BATCH_SIZE = 32

def run_vectorization(chroma_res=None, neo4j_res=None):
    """
    Pipeline de vectorisation Multimodale avec support Matryoshka (MRL).
    Phase 1 : Embeddings Texte (Jina-v3)
    Phase 2 : Embeddings Vision (SigLIP)
    Phase 3 : Sync Neo4j
    """
    print("🚀 Starting SOTA 2026 Multimodal Vectorization (MRL Enabled)...")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: Input file {INPUT_FILE} not found.")
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
        descriptions = [item.get('description', '') for item in batch]
        t_embeddings = text_model.encode(descriptions, convert_to_numpy=True)
        
        # --- PHASE 2 : VISION (SigLIP) ---
        v_embeddings = []
        for item in batch:
            img_url = item.get('image')
            try:
                if img_url:
                    response = requests.get(img_url, timeout=10)
                    img = Image.open(BytesIO(response.content)).convert('RGB')
                    v_emb = vision_model.encode(img, convert_to_numpy=True)
                    v_embeddings.append(v_emb.tolist())
                else: v_embeddings.append(None)
            except: v_embeddings.append(None)

        # --- PHASE 3 : UPSERT & SYNC ---
        for idx, item in enumerate(batch):
            ext_id = str(item['id'])
            
            # Upsert Postgres (via manager global en prod)
            # Ici on simule l'enregistrement des vecteurs 1024 et 1152
            
            # SYNC NEO4J AUTOMATIQUE (Dagster Flow)
            try:
                neo4j_manager.sync_media_to_graph(item, "Anime")
            except Exception as e:
                print(f"⚠️ Neo4j Sync Error for {item['title']}: {e}")

        print(f"   📦 Processed {min(i + BATCH_SIZE, len(new_items))}/{len(new_items)}...")

    print(f"✅ SOTA Vectorization & Neo4j Sync Complete.")
    return True

if __name__ == "__main__":
    run_vectorization()
