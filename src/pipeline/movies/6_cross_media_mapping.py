import json
import os
import sys
import logging

logger = logging.getLogger("animetix." + __name__)

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(BASE_DIR, 'pipeline'))
from chroma_client import chroma_manager

logger.info("🔗 Starting Cross-Media Mapping (Anime/Manga <-> Movies) via ChromaDB...")

# Fichiers de sortie
MAP_ANIME_MOVIE = os.path.join(BASE_DIR, 'data', 'artifacts', 'anime_to_movie_map.json')
MAP_MANGA_MOVIE = os.path.join(BASE_DIR, 'data', 'artifacts', 'manga_to_movie_map.json')

def create_mapping_v2(source_coll_name, target_coll_name, output_path):
    logger.info(f"   - Mapping {source_coll_name} to {target_coll_name}...")
    
    try:
        source_coll = chroma_manager.get_collection(source_coll_name)
        target_coll = chroma_manager.get_collection(target_coll_name)
        
        # On récupère tous les IDs et embeddings de la source
        source_data = source_coll.get(include=['embeddings', 'metadatas'])
        if not source_data['ids']:
            logger.warning(f"⚠️ Source collection {source_coll_name} is empty.")
            return

        mapping = {}
        BATCH_SIZE = 50
        ids = source_data['ids']
        embeddings = source_data['embeddings']
        metadatas = source_data['metadatas']

        for i in range(0, len(ids), BATCH_SIZE):
            batch_end = i + BATCH_SIZE
            batch_embeddings = embeddings[i:batch_end]
            batch_meta = metadatas[i:batch_end]

            results = target_coll.query(query_embeddings=batch_embeddings, n_results=20)

            for j, source_id in enumerate(ids[i:batch_end]):
                source_title = batch_meta[j].get('title')
                matches = {"movie": None, "series": None, "cartoon": None}
                target_metas = results['metadatas'][j]
                target_distances = results['distances'][j]

                for k, m in enumerate(target_metas):
                    m_type = m.get('type', 'Movie').lower()
                    if m_type in matches and matches[m_type] is None:
                        matches[m_type] = {
                            "title": m['title'], "image": m['image'],
                            "score": round((1 - target_distances[k]) * 100, 2)
                        }
                    if all(v is not None for v in matches.values()): break
                mapping[source_title] = matches

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Mapping saved to {output_path}")
    except Exception as e:
        logger.error(f"⚠️ Error mapping {source_coll_name}: {e}")

# Exécution
create_mapping_v2("anime_thematic", "movie_thematic", MAP_ANIME_MOVIE)
create_mapping_v2("manga_thematic", "movie_thematic", MAP_MANGA_MOVIE)
