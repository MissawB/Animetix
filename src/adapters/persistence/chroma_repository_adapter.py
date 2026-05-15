import os
import orjson
import numpy as np
import logging
from chromadb import PersistentClient
from core.ports.repository_port import RepositoryPort
from typing import Optional, Dict, List
from sklearn.metrics.pairwise import cosine_similarity

from django.core.cache import cache

logger = logging.getLogger('animetix')

class ChromaRepositoryAdapter(RepositoryPort):
    def __init__(self, db_path: str, project_root: str):
        self.client = PersistentClient(path=db_path)
        self.project_root = project_root
        self._embedding_fn = None
        
        self.db_files = {
            'Anime': 'data/processed/clean_root_animes.json', 
            'Manga': 'data/processed/clean_root_mangas.json', 
            'Character': 'data/processed/filtered_characters.json',
            'Movie': 'data/processed/clean_root_movies.json',
            'Game': 'data/processed/clean_root_games.json',
            'Actor': 'data/processed/clean_root_actors.json'
        }
        self.coll_names = {
            'Anime': 'anime_thematic', 
            'Manga': 'manga_thematic', 
            'Character': 'character_vibe',
            'Movie': 'movie_thematic',
            'Game': 'game_thematic',
            'Actor': 'actor_vibe'
        }
        self._catalog_cache: Dict[str, Dict] = {}

    @property
    def embedding_fn(self):
        if self._embedding_fn is None:
            # --- SOTA 2026 EMBEDDINGS (Jina-v3) ---
            from chromadb.utils import embedding_functions
            self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="jinaai/jina-embeddings-v3",
                trust_remote_code=True
            )
        return self._embedding_fn

    def get_nearest_neighbors(self, collection_name: str, item_id: str, n_results: int = 5) -> Optional[Dict]:
        try:
            coll = self.client.get_or_create_collection(name=collection_name, embedding_function=self.embedding_fn)
            item_data = coll.get(ids=[str(item_id)], include=['embeddings'])
            embeddings = item_data.get('embeddings')
            if not embeddings:
                return None
            return coll.query(query_embeddings=embeddings, n_results=n_results)
        except Exception as e:
            logger.error(f"Chroma Error in get_nearest_neighbors: {e}")
            return None

    def calculate_similarity(self, collection_name: str, item_a_id: str, item_b_id: str) -> float:
        # --- SIMILARITY CACHE (Redis) ---
        cache_key = f"sim_{collection_name}_{min(item_a_id, item_b_id)}_{max(item_a_id, item_b_id)}"
        cached_val = cache.get(cache_key)
        if cached_val is not None:
            return float(cached_val)
            
        try:
            coll = self.client.get_or_create_collection(name=collection_name, embedding_function=self.embedding_fn)
            res = coll.get(ids=[str(item_a_id), str(item_b_id)], include=['embeddings'])
            if len(res['embeddings']) == 2:
                # Slicing Matryoshka : Utilisation des 256 premières dimensions (Jina-v3 compatible)
                vec1 = np.array(res['embeddings'][0])[:256].reshape(1, -1)
                vec2 = np.array(res['embeddings'][1])[:256].reshape(1, -1)
                score = float(cosine_similarity(vec1, vec2)[0][0])
                
                # Mise en cache pour 7 jours (les embeddings changent peu)
                cache.set(cache_key, score, timeout=3600*24*7)
                return score
        except Exception as e:
            logger.error(f"Chroma Similarity Error between {item_a_id} and {item_b_id}: {e}")
        return 0.0

    def load_catalog(self, media_type: str) -> Optional[Dict]:
        if media_type not in self.db_files:
            return None
            
        if media_type in self._catalog_cache:
            return self._catalog_cache[media_type]

        try:
            db_path = os.path.join(self.project_root, self.db_files[media_type])
            with open(db_path, 'rb') as f: 
                db_content = orjson.loads(f.read())
            
            try:
                coll = self.client.get_or_create_collection(name=self.coll_names[media_type], embedding_function=self.embedding_fn)
                res = coll.get(include=['metadatas'])
            except:
                res = {"metadatas": []}

            catalog = {
                "lookup": res['metadatas'],
                "db": db_content,
                "id_to_full_data": {str(item['id']): item for item in db_content}
            }
            self._catalog_cache[media_type] = catalog
            return catalog
        except Exception as e:
            logger.error(f"Catalog Load Error for {media_type}: {e}")
            return None

    def upsert_items(self, collection_name: str, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict]):
        try:
            coll = self.client.get_or_create_collection(name=collection_name)
            coll.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas)
        except Exception as e:
            logger.error(f"Chroma Upsert Error in {collection_name}: {e}")

    def delete_collection(self, collection_name: str):
        try:
            self.client.delete_collection(name=collection_name)
        except Exception as e:
            logger.error(f"Chroma Delete Error for {collection_name}: {e}")

    def get_collection_count(self, collection_name: str) -> int:
        try:
            coll = self.client.get_collection(name=collection_name)
            return coll.count()
        except:
            return 0

    def get_all_ids(self, collection_name: str) -> List[str]:
        try:
            coll = self.client.get_or_create_collection(name=collection_name)
            return coll.get().get('ids', [])
        except:
            return []

    def get_media_item(self, media_type: str, external_id: str) -> Optional[Dict]:
        catalog = self.load_catalog(media_type)
        if catalog:
            return catalog['id_to_full_data'].get(str(external_id))
        return None

    def get_catalog_by_type(self, media_type: str, limit: int = 1000) -> List[Dict]:
        catalog = self.load_catalog(media_type)
        if catalog:
            return list(catalog['id_to_full_data'].values())[:limit]
        return []

    def load_themes(self) -> Dict:
        """Charge les thèmes depuis les artefacts."""
        path = os.path.join(self.project_root, "data", "processed", "anime_themes.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return orjson.loads(f.read())
        return {}

    def load_covers(self) -> Dict:
        """Charge les couvertures depuis les artefacts."""
        path = os.path.join(self.project_root, "data", "processed", "manga_covers.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return orjson.loads(f.read())
        return {}

    def search_media_items(self, query: str, media_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        return []
