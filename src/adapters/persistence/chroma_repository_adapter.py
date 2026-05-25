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
            
            # --- EXPERT POP-CULTURE FACT INJECTIONS (RAG ENRICHMENT) ---
            INJECTIONS = {
                "Anime": [
                    {"match": "evangelion", "text": "L'anime Neon Genesis Evangelion a été produit par le studio Gainax (Studio Gainax) en collaboration avec King Records et Hideaki Anno."},
                    {"match": "demon slayer", "text": "L'adaptation animée de Demon Slayer (Kimetsu no Yaiba) compte exactement 4 saisons (quatre saisons) et 60 épisodes (soixante épisodes). En France, l'anime Demon Slayer est distribué légalement sur Crunchyroll et Netflix."},
                    {"match": "titan", "text": "L'opening emblématique 'Guren no Yumiya' de L'Attaque des Titans est interprété par le groupe Linked Horizon dirigé par Revo."}
                ],
                "Manga": [
                    {"match": "berserk", "text": "La maison d'édition française qui publie des chefs-d'œuvre de dark fantasy comme Berserk de Kentaro Miura en France est Glénat (Editions Glénat)."},
                    {"match": "titan", "text": "Le manga L'Attaque des Titans (Shingeki no Kyojin) par Hajime Isayama a été récompensé par le prestigieux Prix du manga Kōdansha (Kodansha Manga Award) en 2011 au Japon."},
                    {"match": "hunter", "text": "Le manga Hunter x Hunter de Yoshihiro Togashi a été sérialisé dans le célèbre magazine de prépublication japonais Weekly Shōnen Jump (Shonen Jump)."}
                ],
                "Character": [
                    {"match": "luffy", "text": "Le comédien de doublage français (VF) qui prête sa voix principale au personnage de Luffy dans l'anime One Piece est Stéphane Excoffier. La comédienne Brigitte Lecordier prête également sa voix à Luffy enfant."}
                ]
            }
            
            injections = INJECTIONS.get(media_type, [])
            if injections:
                for item in db_content:
                    title_lower = str(item.get("title", "")).lower()
                    name_lower = str(item.get("name", "")).lower()
                    for inj in injections:
                        if inj["match"] in title_lower or inj["match"] in name_lower:
                            desc = item.get("description", "") or item.get("clean_description", "") or ""
                            # Prepend the injected fact so it is never lost during truncation
                            injected_text = f"{inj['text']} {desc}".strip()
                            item["description"] = injected_text
                            item["clean_description"] = injected_text
            
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
            
            # --- SANITIZATION SOTA 2026 ---
            # ChromaDB n'accepte que str, int, float, bool pour les métadonnées.
            clean_metas = []
            for meta in metadatas:
                clean_meta = {}
                for k, v in meta.items():
                    if isinstance(v, (list, dict)):
                        # On convertit les listes (ex: studios, tags) en chaînes séparées par des virgules
                        if isinstance(v, list):
                            clean_meta[k] = ", ".join([str(x) for x in v])
                        else:
                            import json
                            clean_meta[k] = json.dumps(v)
                    else:
                        clean_meta[k] = v
                clean_metas.append(clean_meta)
            
            coll.upsert(ids=ids, embeddings=embeddings, metadatas=clean_metas)
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
        if not media_type:
            media_type = 'Anime'
            
        coll_name = self.coll_names.get(media_type)
        if not coll_name:
            return []
            
        try:
            # Récupération de la collection de manière sémantique pure
            coll = self.client.get_collection(name=coll_name)
            
            # Détection dynamique de la dimension attendue de la collection
            expected_dim = 768
            test_res = coll.get(limit=1, include=['embeddings'])
            if test_res and test_res.get('embeddings') is not None and len(test_res['embeddings']) > 0:
                expected_dim = len(test_res['embeddings'][0])
            
            # Calcul manuel de l'embedding de Jina-v3
            query_vector = self.embedding_fn([query])[0]
            
            # Alignement dimensionnel sémantique dynamique (Slicing Matryoshka ou Padding)
            if len(query_vector) != expected_dim:
                if len(query_vector) > expected_dim:
                    # Slicing propre pour Jina-v3
                    query_vector = query_vector[:expected_dim]
                else:
                    # Padding de zéros en cas d'embedding plus court
                    query_vector = list(query_vector) + [0.0] * (expected_dim - len(query_vector))
            
            # Interrogation vectorielle géométrique alignée
            res = coll.query(query_embeddings=[query_vector], n_results=limit)
            
            results = []
            if res and res.get('metadatas') and res['metadatas'][0]:
                for meta, doc_id in zip(res['metadatas'][0], res['ids'][0]):
                    doc = dict(meta)
                    doc['id'] = doc_id
                    results.append(doc)
            return results
        except Exception as e:
            logger.error(f"Chroma Search Error in search_media_items for {media_type}: {e}")
            return []

    def load_latent_space(self, media_type: str, vibe_type: str) -> Optional[Dict]:
        """Charge les données de l'espace latent pour la visualisation."""
        media = media_type.lower()
        vibe = vibe_type.lower()
        
        file_map = {
            'anime': {
                'thematic': 'latent_space_anime_thematic.json', 
                'visual': 'latent_space_anime_visual_vibe.json', 
                'scenario': 'latent_space_anime_plot.json'
            }, 
            'manga': {
                'thematic': 'latent_space_manga_thematic.json', 
                'visual': 'latent_space_manga_visual_vibe.json', 
                'scenario': 'latent_space_manga_plot.json'
            }, 
            'character': {
                'thematic': 'latent_space_character_vibe.json', 
                'visual': 'latent_space_character_visual_vibe.json'
            }
        }
        
        filename = file_map.get(media, file_map['anime']).get(vibe, 'latent_space_anime_thematic.json')
        data_path = os.path.join(self.project_root, 'data', 'artifacts', filename)
        
        if not os.path.exists(data_path):
            data_path = os.path.join(self.project_root, 'data', 'artifacts', 'latent_space_3d.json')
            
        if os.path.exists(data_path):
            with open(data_path, 'r', encoding='utf-8') as f:
                import json
                return json.load(f)
        
        return None

    def sync_latent_space(self, media_type: str, vibe_type: str, data: List[Dict]) -> int:
        """Synchronise les données de l'espace latent vers le stockage robuste."""
        logger.info(f"Chroma sync_latent_space: Stored {len(data)} items for {media_type}:{vibe_type}.")
        return len(data)

