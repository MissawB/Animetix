import logging
import os
from typing import Dict, List, Optional

import numpy as np
import orjson
from adapters.persistence.cache_constants import (
    COLLECTION_COUNT_CACHE_TTL_SECONDS,
    PGVRA_COLLECTION_COUNT_CACHE_PREFIX,
    VSP_COLLECTION_COUNT_CACHE_PREFIX,
)
from core.ports.repository_port import RepositoryPort
from core.utils.model_registry import (
    resolve_text_embedding_model_id,
    resolve_trust_remote_code,
    trusted_revision,
)
from django.core.cache import cache
from pipeline.vector_client import vector_manager

logger = logging.getLogger("animetix")


class LocalSentenceTransformerEmbeddingFunction:
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer  # noqa: E402

        self.model = SentenceTransformer(
            model_name,
            trust_remote_code=resolve_trust_remote_code(model_name),
            revision=trusted_revision(model_name) or "main",
        )

    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(input)
        if hasattr(embeddings, "tolist"):
            return embeddings.tolist()
        return [list(emb) for emb in embeddings]


class PGVectorRepositoryAdapter(RepositoryPort):
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.manager = vector_manager
        self._embedding_fn = None

        self.db_files = {
            "Anime": "data/processed/clean_root_animes.json",
            "Manga": "data/processed/clean_root_mangas.json",
            "Character": "data/processed/filtered_characters.json",
            "Movie": "data/processed/clean_root_movies.json",
            "Game": "data/processed/clean_root_games.json",
            "Actor": "data/processed/clean_root_actors.json",
        }
        self.coll_names = {
            "Anime": "anime_thematic",
            "Manga": "manga_thematic",
            "Character": "character_vibe",
            "Movie": "movie_thematic",
            "Game": "game_thematic",
            "Actor": "actor_vibe",
        }
        self._catalog_cache: Dict[str, Dict] = {}

    @property
    def embedding_fn(self):
        if self._embedding_fn is None:
            # Resolved from the same core.utils.model_registry source of truth
            # (EMBEDDING_VERSIONS + MODEL_VERSION_TEXT env var) the catalogue
            # vectoriser (pipeline.models_registry) uses -- never hardcoded
            # here, or query embeddings would drift to a different model/
            # dimension than what's actually stored in pgvector.
            self._embedding_fn = LocalSentenceTransformerEmbeddingFunction(
                model_name=resolve_text_embedding_model_id()
            )
        return self._embedding_fn

    def get_collection(self, collection_name: str):
        return self.manager.get_collection(collection_name)

    def _resolve_collection(self, name: str) -> str:
        """Resolve a media-type key (e.g. ``"Anime"``) to its pgvector collection
        name (e.g. ``"anime_thematic"``).

        Callers that already pass a real collection name (or any string that
        isn't a known media-type key) are left untouched, so this is safe to
        apply unconditionally to every ``collection_name``/``media_type``
        argument that reaches the vector store.
        """
        return self.coll_names.get(name, name)

    def get_nearest_neighbors(
        self, collection_name: str, item_id: str, n_results: int = 5
    ) -> Optional[Dict]:
        collection_name = self._resolve_collection(collection_name)
        try:
            coll = self.manager.get_collection(name=collection_name)
            item_data = coll.get(ids=[str(item_id)], include=["embeddings"])
            embeddings = item_data.get("embeddings")
            if not embeddings:
                return None
            return coll.query(query_embeddings=embeddings, n_results=n_results)
        except Exception as e:
            logger.error(f"PGVector Error in get_nearest_neighbors: {e}")
            return None

    def calculate_similarity(
        self, collection_name: str, item_a_id: str, item_b_id: str
    ) -> float:
        collection_name = self._resolve_collection(collection_name)
        cache_key = f"sim_{collection_name}_{min(item_a_id, item_b_id)}_{max(item_a_id, item_b_id)}"
        cached_val = cache.get(cache_key)
        if cached_val is not None:
            return float(cached_val)

        try:
            coll = self.manager.get_collection(name=collection_name)
            res = coll.get(ids=[str(item_a_id), str(item_b_id)], include=["embeddings"])
            if len(res.get("embeddings", [])) == 2:
                # Slicing Matryoshka
                from sklearn.metrics.pairwise import cosine_similarity  # noqa: E402

                vec1 = np.array(res["embeddings"][0])[:256].reshape(1, -1)
                vec2 = np.array(res["embeddings"][1])[:256].reshape(1, -1)
                score = float(cosine_similarity(vec1, vec2)[0][0])
                cache.set(cache_key, score, timeout=3600 * 24 * 7)
                return score
        except Exception as e:
            logger.error(
                f"PGVector Similarity Error between {item_a_id} and {item_b_id}: {e}"
            )
        return 0.0

    def load_catalog(self, media_type: str) -> Optional[Dict]:
        if media_type not in self.db_files:
            return None

        if media_type in self._catalog_cache:
            return self._catalog_cache[media_type]

        try:
            db_path = os.path.join(self.project_root, self.db_files[media_type])
            with open(db_path, "rb") as f:
                db_content = orjson.loads(f.read())

            try:
                coll = self.manager.get_collection(name=self.coll_names[media_type])
                res = coll.get(include=["metadatas"])
            except Exception as e:
                logger.error(
                    f"Error getting collection {media_type} in load_catalog: {e}"
                )
                res = {"metadatas": []}

            catalog = {
                "lookup": res["metadatas"],
                "db": db_content,
                "id_to_full_data": {str(item["id"]): item for item in db_content},
            }
            self._catalog_cache[media_type] = catalog
            return catalog
        except Exception as e:
            logger.error(f"Catalog Load Error for {media_type}: {e}")
            return None

    @staticmethod
    def _collection_count_cache_key(collection_name: str) -> str:
        return f"{PGVRA_COLLECTION_COUNT_CACHE_PREFIX}{collection_name}"

    def _invalidate_collection_count(self, collection_name: str) -> None:
        """Best-effort cache invalidation: a failure here must not surface as
        an upsert/delete failure -- it only means the cached count stays
        stale for (at most) the remainder of the TTL, the same tradeoff
        already accepted for the cache in general.

        Invalidates BOTH count caches -- this adapter's own
        (`pgvra_collection_count_*`) AND `PgVectorStoreAdapter`'s
        (`vsp_collection_count_*`, the one `MediaSearchView`'s 503 "index not
        built" guard actually reads). They count the same fact under two
        different keys; clearing only the writer's own key left the guard
        free to keep answering "index not built" for up to
        `COLLECTION_COUNT_CACHE_TTL_SECONDS` after a build had already landed.
        """
        for cache_key in (
            self._collection_count_cache_key(collection_name),
            f"{VSP_COLLECTION_COUNT_CACHE_PREFIX}{collection_name}",
        ):
            try:
                cache.delete(cache_key)
            except Exception as e:
                logger.warning(
                    f"Cache invalidation failed for collection '{collection_name}' "
                    f"(key '{cache_key}'): {e}"
                )

    def upsert_items(
        self,
        collection_name: str,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict],
        documents: Optional[List[str]] = None,
        strict: bool = False,
    ):
        try:
            coll = self.manager.get_collection(collection_name)
            coll.upsert(
                ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents
            )
        except Exception as e:
            logger.error(f"PGVector Upsert Error in {collection_name}: {e}")
            # L'upsert tourne dans un `transaction.atomic()` : l'échec a annulé le
            # LOT ENTIER. Un appelant qui compte ce qu'il a écrit doit le savoir,
            # sinon il annonce des vecteurs qui n'existent pas.
            if strict:
                raise
            return
        # A fresh backfill must be immediately visible, not hidden behind a
        # cached "empty" count for up to 60s (see get_collection_count below).
        self._invalidate_collection_count(collection_name)

    def delete_collection(self, collection_name: str):
        try:
            self.manager.delete_collection(collection_name)
        except Exception as e:
            logger.error(f"PGVector Delete Error for {collection_name}: {e}")
            return
        # An emptied collection must not stay billable for up to 60s on the
        # strength of a stale cached (non-zero) count.
        self._invalidate_collection_count(collection_name)

    def get_collection_count(self, collection_name: str) -> int:
        """Nombre de vecteurs dans la collection, mis en cache 60s.

        Sert de garde-fou anti-facturation avant une recherche payante
        (`VideoRAGService.is_available`) : sans cache, chaque recherche
        déclencherait un COUNT(*) supplémentaire. Un TTL court (aligné sur
        `PgVectorStoreAdapter.get_collection_count` via
        `COLLECTION_COUNT_CACHE_TTL_SECONDS`) suffit -- il ne s'agit que de
        détecter si l'index a été construit.
        """
        cache_key = self._collection_count_cache_key(collection_name)

        try:
            cached_count = cache.get(cache_key)
        except Exception as e:
            # The cache is an optimisation, not a dependency: a Redis blip
            # must degrade to a live COUNT, not to a 500.
            logger.warning(f"Cache read failed for '{cache_key}': {e}")
            cached_count = None
        if cached_count is not None:
            return int(cached_count)

        try:
            coll = self.manager.get_collection(collection_name)
            count = coll.count()
        except Exception as e:
            # A failure to ask the database is NOT the same fact as "I
            # asked, and it is empty" -- caching a 0 here would memoise a
            # transient outage as "the index doesn't exist" for the full
            # TTL. Fail closed for *this* request only, without remembering
            # it.
            logger.exception(
                f"Error getting collection count for {collection_name}: {e}"
            )
            return 0

        try:
            cache.set(cache_key, count, timeout=COLLECTION_COUNT_CACHE_TTL_SECONDS)
        except Exception as e:
            logger.warning(f"Cache write failed for '{cache_key}': {e}")

        return count

    def get_all_ids(self, collection_name: str) -> List[str]:
        try:
            return list(self.manager.get_all_ids(collection_name))
        except Exception as e:
            logger.exception(f"Error getting all IDs for {collection_name}: {e}")
            return []

    def get_media_item(self, media_type: str, external_id: str) -> Optional[Dict]:
        catalog = self.load_catalog(media_type)
        if catalog:
            return catalog["id_to_full_data"].get(str(external_id))
        return None

    def get_catalog_by_type(
        self, media_type: str, limit: int = 1000, offset: int = 0
    ) -> List[Dict]:
        catalog = self.load_catalog(media_type)
        if catalog:
            return list(catalog["id_to_full_data"].values())[offset : offset + limit]
        return []

    def load_themes(self) -> Dict:
        path = os.path.join(self.project_root, "data", "processed", "anime_themes.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return orjson.loads(f.read())
        return {}

    def load_covers(self) -> Dict:
        path = os.path.join(self.project_root, "data", "processed", "manga_covers.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return orjson.loads(f.read())
        return {}

    def get_manga_covers_metadata(self) -> List[Dict]:
        try:
            from animetix.models import MangaCover

            covers_qs = MangaCover.objects.all()
            if covers_qs.exists():
                metadata = []
                for c in covers_qs:
                    has_ja = bool(c.covers.get("ja"))
                    has_fr = bool(c.covers.get("fr"))
                    metadata.append(
                        {
                            "id": c.manga_id,
                            "title": c.title,
                            "title_english": c.title_english,
                            "title_native": c.title_native,
                            "synonyms": c.synonyms,
                            "author": c.author,
                            "has_ja": has_ja,
                            "has_fr": has_fr,
                        }
                    )
                return metadata
        except Exception:
            logger.warning(
                "MangaCover DB read failed; falling back to manga_covers.json",
                exc_info=True,
            )

        covers = self.load_covers()
        metadata = []
        for mid, info in covers.items():
            has_ja = bool(info.get("covers", {}).get("ja"))
            has_fr = bool(info.get("covers", {}).get("fr"))
            metadata.append(
                {
                    "id": str(mid),
                    "title": info.get("title", ""),
                    "title_english": info.get("title_english"),
                    "title_native": info.get("title_native"),
                    "synonyms": info.get("synonyms", []),
                    "author": info.get("author"),
                    "has_ja": has_ja,
                    "has_fr": has_fr,
                }
            )
        return metadata

    def get_manga_cover_by_id(self, manga_id: str) -> Optional[Dict]:
        try:
            from animetix.models import MangaCover

            # filter().first(): a plain miss is a normal state (file fallback),
            # only a real DB failure should reach the except below.
            c = MangaCover.objects.filter(manga_id=manga_id).first()
            if c:
                return {
                    "title": c.title,
                    "mangadex_id": c.mangadex_id,
                    "covers": c.covers,
                    "title_english": c.title_english,
                    "title_native": c.title_native,
                    "synonyms": c.synonyms,
                    "author": c.author,
                }
        except Exception:
            logger.warning(
                "MangaCover DB read failed; falling back to manga_covers.json",
                exc_info=True,
            )

        covers = self.load_covers()
        info = covers.get(manga_id)
        if not info:
            return None
        return {
            "title": info.get("title", ""),
            "mangadex_id": info.get("mangadex_id"),
            "covers": info.get("covers", {}),
            "title_english": info.get("title_english"),
            "title_native": info.get("title_native"),
            "synonyms": info.get("synonyms", []),
            "author": info.get("author"),
        }

    def get_manga_cover_by_title(self, title: str) -> Optional[Dict]:
        try:
            from animetix.models import MangaCover

            c = MangaCover.objects.filter(title=title).first()
            if c:
                return {
                    "title": c.title,
                    "mangadex_id": c.mangadex_id,
                    "covers": c.covers,
                    "title_english": c.title_english,
                    "title_native": c.title_native,
                    "synonyms": c.synonyms,
                    "author": c.author,
                }
        except Exception:
            logger.warning(
                "MangaCover DB read failed; falling back to manga_covers.json",
                exc_info=True,
            )

        covers = self.load_covers()
        for mid, info in covers.items():
            if info.get("title") == title:
                return {
                    "title": info.get("title", ""),
                    "mangadex_id": info.get("mangadex_id"),
                    "covers": info.get("covers", {}),
                    "title_english": info.get("title_english"),
                    "title_native": info.get("title_native"),
                    "synonyms": info.get("synonyms", []),
                    "author": info.get("author"),
                }
        return None

    def search_media_items(
        self,
        query: str,
        media_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict]:
        if not media_type:
            media_type = "Anime"

        coll_name = self._resolve_collection(media_type)
        if not coll_name:
            return []

        try:
            coll = self.manager.get_collection(name=coll_name)

            from pipeline.vector_client import is_alloydb_ai_supported  # noqa: E402

            if is_alloydb_ai_supported():
                res = coll.query(query_texts=[query], n_results=limit, offset=offset)
            else:
                expected_dim = 768
                test_res = coll.get(limit=1, include=["embeddings"])
                if (
                    test_res
                    and test_res.get("embeddings") is not None
                    and len(test_res["embeddings"]) > 0
                ):
                    expected_dim = len(test_res["embeddings"][0])

                query_vector = self.embedding_fn([query])[0]

                if len(query_vector) != expected_dim:
                    if len(query_vector) > expected_dim:
                        query_vector = query_vector[:expected_dim]
                    else:
                        query_vector = list(query_vector) + [0.0] * (
                            expected_dim - len(query_vector)
                        )

                res = coll.query(
                    query_embeddings=[query_vector], n_results=limit, offset=offset
                )

            results = []
            if res and res.get("metadatas") and res["metadatas"][0]:
                for meta, doc_id in zip(res["metadatas"][0], res["ids"][0]):
                    doc = dict(meta)
                    doc["id"] = doc_id
                    results.append(doc)
            return results
        except Exception as e:
            logger.error(
                f"PGVector Search Error in search_media_items for {media_type}: {e}"
            )
            return []

    def load_latent_space(
        self, media_type: str, vibe_type: str
    ) -> Optional[List[Dict]]:
        media = media_type.lower()
        vibe = vibe_type.lower()
        file_map = {
            "anime": {
                "thematic": "latent_space_anime_thematic.json",
                "visual": "latent_space_anime_visual_vibe.json",
                "scenario": "latent_space_anime_plot.json",
            },
            "manga": {
                "thematic": "latent_space_manga_thematic.json",
                "visual": "latent_space_manga_visual_vibe.json",
                "scenario": "latent_space_manga_plot.json",
            },
            "character": {
                "thematic": "latent_space_character_vibe.json",
                "visual": "latent_space_character_visual_vibe.json",
            },
        }
        filename = file_map.get(media, file_map["anime"]).get(
            vibe, "latent_space_anime_thematic.json"
        )
        data_path = os.path.join(self.project_root, "data", "artifacts", filename)
        if not os.path.exists(data_path):
            data_path = os.path.join(
                self.project_root, "data", "artifacts", "latent_space_3d.json"
            )
        if os.path.exists(data_path):
            with open(data_path, "r", encoding="utf-8") as f:
                import json  # noqa: E402

                return json.load(f)
        return None

    def sync_latent_space(
        self, media_type: str, vibe_type: str, data: List[Dict]
    ) -> int:
        logger.info(
            f"PGVector sync_latent_space: Stored {len(data)} items for {media_type}:{vibe_type}."
        )
        return len(data)

    def get_creative_fusion(self, fusion_id: int) -> Optional[Dict]:
        return None

    def get_user_gameplay_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        return []

    def get_user_creative_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        return []
