from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class RepositoryPort(ABC):
    @abstractmethod
    def get_nearest_neighbors(
        self, collection_name: str, item_id: str, n_results: int = 5
    ) -> Optional[Dict]:
        pass

    @abstractmethod
    def load_catalog(self, media_type: str) -> Optional[Dict]:
        pass

    @abstractmethod
    def load_themes(self) -> Dict:
        pass

    @abstractmethod
    def load_covers(self) -> Dict:
        pass

    @abstractmethod
    def calculate_similarity(
        self, collection_name: str, item_a_id: str, item_b_id: str
    ) -> float:
        pass

    @abstractmethod
    def upsert_items(
        self,
        collection_name: str,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict],
        documents: Optional[List[str]] = None,
        strict: bool = False,
    ):
        """Ajoute ou met à jour des items dans une collection vectorielle.

        `strict=False` (le défaut historique) : une écriture qui échoue est
        journalisée et la main est rendue — les pipelines de masse préfèrent
        continuer plutôt que perdre un run entier sur un lot.

        `strict=True` : l'échec est propagé. À utiliser dès que l'appelant COMPTE
        ce qu'il a écrit : sans ça, il compte ce qu'il aurait voulu écrire et
        annonce un succès qui n'a pas eu lieu.
        """
        pass

    @abstractmethod
    def delete_collection(self, collection_name: str):
        """Supprime une collection entière."""
        pass

    @abstractmethod
    def get_collection_count(self, collection_name: str) -> int:
        """Retourne le nombre d'items dans une collection."""
        pass

    @abstractmethod
    def get_all_ids(self, collection_name: str) -> List[str]:
        """Retourne tous les IDs d'une collection."""
        pass

    @abstractmethod
    def get_media_item(self, media_type: str, external_id: str) -> Optional[Dict]:
        """Récupère un item média depuis la source relationnelle."""
        pass

    @abstractmethod
    def get_catalog_by_type(
        self, media_type: str, limit: int = 1000, offset: int = 0
    ) -> List[Dict]:
        """Récupère le catalogue complet depuis la source relationnelle avec pagination."""
        pass

    @abstractmethod
    def search_media_items(
        self,
        query: str,
        media_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict]:
        """Recherche textuelle dans le catalogue relationnel avec pagination."""
        pass

    @abstractmethod
    def load_latent_space(
        self, media_type: str, vibe_type: str
    ) -> Optional[List[Dict]]:
        """Charge les données de l'espace latent pour la visualisation."""
        pass

    @abstractmethod
    def sync_latent_space(
        self, media_type: str, vibe_type: str, data: List[Dict]
    ) -> int:
        """Synchronise les données de l'espace latent vers le stockage robuste."""
        pass

    @abstractmethod
    def get_creative_fusion(self, fusion_id: int) -> Optional[Dict]:
        """Récupère une fusion créative par son ID."""
        pass

    @abstractmethod
    def get_user_gameplay_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Récupère l'historique des sessions de jeu d'un utilisateur."""
        pass

    @abstractmethod
    def get_user_creative_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Récupère l'historique des fusions créatives d'un utilisateur."""
        pass

    @abstractmethod
    def get_manga_covers_metadata(self) -> List[Dict]:
        """Récupère les métadonnées (id, title, aliases, et indicateurs de langue) de toutes les covers de manga."""
        pass

    @abstractmethod
    def get_manga_cover_by_id(self, manga_id: str) -> Optional[Dict]:
        """Récupère l'objet cover d'un manga (avec ses tomes/URLs) par son ID unique."""
        pass

    @abstractmethod
    def get_manga_cover_by_title(self, title: str) -> Optional[Dict]:
        """Récupère l'objet cover d'un manga (avec ses tomes/URLs) par son titre."""
        pass
