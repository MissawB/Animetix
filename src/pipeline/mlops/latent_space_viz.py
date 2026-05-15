import json
import os
import sys
import numpy as np
from dagster import asset

# Forcer l'encodage UTF-8 pour éviter les erreurs sur Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Chemins
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACTS_DIR = os.path.join(BASE_DIR, 'data', 'artifacts')

@asset(group_name="mlops", deps=["anime_artifacts", "manga_artifacts", "character_artifacts"])
def latent_space_data_multi():
    """Projette les embeddings de différentes collections en 3D via UMAP."""
    # IMPORT DYNAMIQUE pour éviter de bloquer Dagster si la lib est absente
    try:
        import umap
    except ImportError:
        raise Exception("❌ La bibliothèque 'umap-learn' est requise. Installez-la avec: pip install umap-learn")

    # Import dynamique du chroma manager
    sys.path.append(os.path.join(BASE_DIR, 'pipeline'))
    from chroma_client import chroma_manager

    # Préchargement des bases de données locales pour mapping (Fallback si metadata absente)
    print("📂 Loading local databases for metadata mapping...")
    db_paths = {
        "anime": os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_animes.json'),
        "manga": os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_mangas.json'),
        "character": os.path.join(BASE_DIR, 'data', 'processed', 'filtered_characters.json'),
        "movie": os.path.join(BASE_DIR, 'pipeline', 'movies', 'data', 'raw', 'raw_tmdb_db.json')
    }
    
    id_to_genre = {}
    for key, path in db_paths.items():
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    db = json.load(f)
                    for item in db:
                        item_id = str(item.get('id'))
                        if key == 'character':
                            affiliations = item.get('metadata', {}).get('affiliations', [])
                            id_to_genre[item_id] = affiliations[0] if affiliations else "Character"
                        else:
                            genres = item.get('genres', [])
                            id_to_genre[item_id] = genres[0] if genres else key.capitalize()
            except Exception as e:
                print(f"⚠️ Warning loading {path}: {e}")

    collections = [
        ("anime_thematic", "latent_space_anime_thematic.json"),
        ("anime_visual_vibe", "latent_space_anime_visual_vibe.json"),
        ("anime_plot", "latent_space_anime_plot.json"),
        ("manga_thematic", "latent_space_manga_thematic.json"),
        ("manga_visual_vibe", "latent_space_manga_visual_vibe.json"),
        ("manga_plot", "latent_space_manga_plot.json"),
        ("movie_thematic", "latent_space_movie_thematic.json"),
        ("movie_plot", "latent_space_movie_plot.json"),
        ("character_vibe", "latent_space_character_vibe.json"),
        ("character_visual_vibe", "latent_space_character_visual_vibe.json")
    ]

    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    for coll_name, filename in collections:
        print(f"🔮 Processing collection: {coll_name}...")
        try:
            coll = chroma_manager.get_collection(coll_name)
            # On prend un échantillon représentatif
            res = coll.get(include=['embeddings', 'metadatas'], limit=1000)

            if res['embeddings'] is None or len(res['embeddings']) == 0:
                print(f"⚠️ No embeddings found in collection '{coll_name}'. Skipping.")
                continue

            embeddings = np.array(res['embeddings'])
            metadatas = res['metadatas']

            print(f"🧩 Computing UMAP 3D projection for {len(embeddings)} points in {coll_name}...")
            # Paramètres UMAP optimisés pour la viz
            reducer = umap.UMAP(n_components=3, n_neighbors=15, min_dist=0.1, random_state=42)
            coords_3d = reducer.fit_transform(embeddings)

            plot_data = []
            for i in range(len(coords_3d)):
                meta = metadatas[i]
                item_id = str(meta.get('id'))
                
                category = "Inconnu"
                if 'genres' in meta and meta.get('genres'):
                    category = meta.get('genres').split(',')[0].strip()
                elif 'affiliations' in meta and meta.get('affiliations'):
                    category = meta.get('affiliations').split(',')[0].strip()
                elif item_id in id_to_genre:
                    category = id_to_genre[item_id]
                elif 'type' in meta:
                    category = meta.get('type')

                plot_data.append({
                    "x": float(coords_3d[i][0]),
                    "y": float(coords_3d[i][1]),
                    "z": float(coords_3d[i][2]),
                    "title": meta.get('title') or meta.get('name') or "Sans titre",
                    "category": category,
                    "image": meta.get('image'),
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

            print(f"✅ Saved to {output_path}")

        except Exception as e:
            print(f"❌ Error processing {coll_name}: {e}")

    return True

if __name__ == "__main__":
    latent_space_data_multi()
