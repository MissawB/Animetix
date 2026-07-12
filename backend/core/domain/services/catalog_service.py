import json
import logging
from typing import Any, Dict, List, Optional

from ...ports.repository_port import RepositoryPort
from ..exceptions import AnimetixError, CatalogNotFoundError, GameLogicError

logger = logging.getLogger("animetix")


class CatalogService:
    """
    Service dédié à la gestion, au chargement et à la mise en cache des catalogues de médias.
    Décharge GameService de la manipulation brute des données.
    """

    def __init__(
        self,
        repository: RepositoryPort,
        sql_repository: Optional[RepositoryPort] = None,
        cache_service=None,
    ):
        self.repository = repository
        self.sql_repository = sql_repository or repository
        self.cache = cache_service
        self._cached_catalogs: Dict[str, Any] = {}
        self._emoji_sequences: Optional[Dict] = None
        self._anime_episodes: Optional[Dict] = None

    def load_data(self, media_type: str) -> Optional[Dict]:
        """Backward compatibility method for AnimetixService.load_data."""
        try:
            return self.get_catalog(media_type)
        except CatalogNotFoundError:
            logger.warning(f"Catalog for {media_type} not found.")
            return None
        except Exception as e:
            logger.error(f"Error loading data for {media_type}: {e}")
            return None

    def get_catalog(self, media_type: str) -> Dict:
        """
        Charge et prépare le catalogue pour un type de média spécifique.
        Gère le cache multiniveau (RAM locale + Redis).
        """
        # 1. Cache RAM (processus courant)
        if media_type in self._cached_catalogs:
            return self._cached_catalogs[media_type]

        # 2. Cache distribué (Redis)
        if self.cache:
            try:
                cached = self.cache.get(f"catalog_{media_type}")
                if cached:
                    self._cached_catalogs[media_type] = cached
                    return cached
            except Exception as e:
                logger.warning(f"Cache retrieval failed for {media_type}: {e}")

        # 3. Chargement depuis les dépôts (SQL ou Fichiers)
        try:
            # Récupération brute des données (limité à 2000 pour les performances de l'UI)
            db = self.sql_repository.get_catalog_by_type(media_type, limit=2000)

            if not db:
                catalog_data = self.repository.load_catalog(media_type)
                if not catalog_data:
                    raise CatalogNotFoundError(media_type)
                db = catalog_data["db"]
                lookup = catalog_data["lookup"]
            else:
                lookup = [{"id": item["id"], "title": item["title"]} for item in db]
                catalog_data = {"db": db, "lookup": lookup}

            # Enrichissement pour accès rapide O(1)
            title_to_data = {
                str(item.get("title") or item.get("name")): item for item in db
            }
            titles = [str(item.get("title") or item.get("name")) for item in db]

            catalog_data.update(
                {
                    "title_to_full_data": title_to_data,
                    "titles": titles,
                    "title_to_index": {t: i for i, t in enumerate(titles)},
                    "id_to_full_data": {str(item["id"]): item for item in db},
                }
            )

            # Préparation de l'autocomplete JSON
            autocomplete_items = [
                {
                    "title": item.get("title") or item.get("name"),
                    "title_english": item.get("title_english"),
                    "image": item.get("image"),
                }
                for item in db
            ]
            catalog_data["autocomplete_json"] = json.dumps(autocomplete_items)

            # 4. Sauvegarde dans les caches
            self._cached_catalogs[media_type] = catalog_data
            if self.cache:
                try:
                    self.cache.set(f"catalog_{media_type}", catalog_data, timeout=3600)
                except Exception as e:
                    logger.error(f"Failed to cache catalog {media_type}: {e}")

            return catalog_data
        except Exception as e:
            if isinstance(e, AnimetixError):
                raise
            raise GameLogicError(
                f"Critical error loading catalog {media_type}: {str(e)}"
            )

    def get_akinetix_attributes(self) -> Dict:
        """Charge les attributs fins Akinetix depuis les fichiers traités."""
        import os  # noqa: E402

        path = os.path.join(
            getattr(self.repository, "project_root", ""),
            "data",
            "processed",
            "akinetix_attributes.json",
        )
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load Akinetix attributes: {e}")
        return {}

    def get_emoji_sequences(self) -> Dict:
        """Charge les séquences d'emojis précalculées (jeu Emoji, CPU).

        Format : {media_type: {id: [emoji, ...]}} — cf.
        ``backend/pipeline/games/build_emoji_sequences.py``. Mis en cache RAM.
        """
        import os  # noqa: E402

        if self._emoji_sequences is not None:
            return self._emoji_sequences
        path = os.path.join(
            getattr(self.repository, "project_root", ""),
            "data",
            "artifacts",
            "emoji_sequences.json",
        )
        data = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load emoji sequences: {e}")
        self._emoji_sequences = data
        return data

    def get_anime_episodes(self) -> Dict:
        """Episode titles and plot summaries, keyed by MAL id (string).

        Produced by ``backend/pipeline/anime/fetch_kitsu_episodes.py``. Kept out of
        MediaItem.metadata on purpose: several thousand synopses would ride along
        with every catalogue load and land in the Redis cache entry.
        """
        import os  # noqa: E402

        if self._anime_episodes is not None:
            return self._anime_episodes
        path = os.path.join(
            getattr(self.repository, "project_root", ""),
            "data",
            "processed",
            "anime_episodes.json",
        )
        data = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load anime episodes: {e}")
        self._anime_episodes = data
        return data

    def invalidate_cache(self, media_type: Optional[str] = None):
        """Invalide le cache pour un type spécifique ou tous les types."""
        if media_type:
            self._cached_catalogs.pop(media_type, None)
            if self.cache:
                self.cache.delete(f"catalog_{media_type}")
        else:
            self._cached_catalogs.clear()
            # Note: On ne vide pas tout Redis pour ne pas impacter les sessions

    def search_items(
        self, query: str, media_type: Optional[str] = None, limit: int = 10
    ) -> List[Dict]:
        """Recherche des éléments dans le catalogue SQL (Source of Truth) pour autocomplétion."""
        try:
            return self.sql_repository.search_media_items(query, media_type, limit)
        except Exception as e:
            logger.error(f"Error in search_items: {e}")
            return []
