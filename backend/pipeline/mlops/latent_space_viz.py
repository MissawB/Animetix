import os
import json
import logging
import numpy as np
from sklearn.manifold import TSNE
from pipeline.chroma_client import chroma_manager

logger = logging.getLogger("animetix.mlops.viz")

ARTIFACTS_DIR = os.path.join("data", "artifacts")

def run_visualization():
    """
    Génère les projections 3D pour TOUTES les collections ChromaDB.
    """
    client = chroma_manager
    collections_to_viz = [
        "anime_plot", "anime_thematic", "anime_visual_vibe",
        "manga_plot", "manga_thematic", "manga_visual_vibe",
        "character_vibe", "character_visual_vibe",
        "movie_plot", "movie_thematic"
    ]

    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    for coll_name in collections_to_viz:
        filename = f"latent_space_{coll_name}.json"
        try:
            coll = client.get_collection(coll_name)
            results = coll.get(include=['embeddings', 'metadatas', 'documents'])
            
            if not results['embeddings'] or len(results['embeddings']) < 5:
                logger.warning(f"⚠️ Collection {coll_name} too small for visualization.")
                continue

            logger.info(f"🔮 Projecting {len(results['embeddings'])} points for {coll_name}...")
            
            embeddings = np.array(results['embeddings'])
            # Normalisation
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / (norms + 1e-9)

            tsne = TSNE(
                n_components=3, 
                perplexity=min(30, len(embeddings)-1), 
                init='pca', 
                learning_rate='auto',
                random_state=42
            )
            coords_3d = tsne.fit_transform(embeddings)

            plot_data = []
            for i in range(len(coords_3d)):
                meta = results['metadatas'][i]
                plot_data.append({
                    "x": float(coords_3d[i][0]),
                    "y": float(coords_3d[i][1]),
                    "z": float(coords_3d[i][2]),
                    "label": meta.get('title') or meta.get('name') or results['documents'][i],
                    "image": meta.get('image') or meta.get('image_url') or "",
                    "franchise": meta.get('franchise', "N/A"),
                    "year": str(meta.get('year', "N/A"))
                })

            output_path = os.path.join(ARTIFACTS_DIR, filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(plot_data, f, indent=2, ensure_ascii=False)
            
            # On garde une version par défaut pour la compatibilité descendante
            if coll_name == "anime_thematic":
                default_path = os.path.join(ARTIFACTS_DIR, 'latent_space_3d.json')
                with open(default_path, 'w', encoding='utf-8') as f:
                    json.dump(plot_data, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Saved to {output_path}")

        except Exception as e:
            logger.error(f"❌ Error processing {coll_name}: {e}")

    return True

if __name__ == "__main__":
    run_visualization()
