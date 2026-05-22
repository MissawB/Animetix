import json
import os
import logging
from typing import List, Dict, Any
from core.ports.inference_port import InferencePort
from pipeline.chroma_client import chroma_manager
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger("animetix.pipeline.combat")

# Project paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
COMBAT_DATA_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'combat_data.json')

def run_combat_vectorization(chroma_res=None):
    """
    Vectorizes combat stats and abilities for semantic search of similar power levels.
    """
    if not os.path.exists(COMBAT_DATA_PATH):
        logger.error(f"❌ {COMBAT_DATA_PATH} not found.")
        return False

    with open(COMBAT_DATA_PATH, 'r', encoding='utf-8') as f:
        combat_data = json.load(f)

    if not combat_data:
        logger.warning("ℹ️ No combat data to vectorize.")
        return True

    logger.info(f"🚀 Vectorizing {len(combat_data)} combat profiles...")

    # Data Preparation
    corpus = []
    metadatas = []
    ids = []

    for item in combat_data:
        stats = item['stats']
        abilities = ", ".join(stats.get('abilities', []))
        summary = item.get('summary', "")
        
        # We create a combat-specific corpus
        combat_text = f"Tier: {stats.get('tier')}. Speed: {stats.get('speed')}. Durability: {stats.get('durability')}. Intelligence: {stats.get('intelligence')}. Abilities: {abilities}. Summary: {summary}"
        
        corpus.append(combat_text)
        metadatas.append({
            "name": item['name'],
            "tier": stats.get('tier'),
            "tier_value": stats.get('tier_value', 0),
            "image_url": item.get('image_url', "")
        })
        ids.append(item['name'])

    # Calculating Embeddings
    model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
    embeddings = model.encode(corpus, show_progress_bar=True)

    # Sync with ChromaDB
    # manager = chroma_res.manager if chroma_res else chroma_manager
    # collection = manager.get_collection("combat_profiles")
    
    # Correction: Use the resource directly
    collection = chroma_res.get_collection("combat_profiles") if chroma_res else chroma_manager.get_collection("combat_profiles")
    
    try:
        collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            metadatas=metadatas
        )
        logger.info("✅ ChromaDB combat profiles synchronization complete.")
    except Exception as e:
        logger.error(f"❌ ChromaDB Error: {e}")
        return False

    return True
