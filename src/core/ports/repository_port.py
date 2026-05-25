from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class RepositoryPort(ABC):
    @abstractmethod
    def get_nearest_neighbors(self, collection_name: str, item_id: str, n_results: int = 5) -> Optional[Dict]:
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
    def calculate_similarity(self, collection_name: str, item_a_id: str, item_b_id: str) -> float:
        pass

    @abstractmethod
    def upsert_items(self, collection_name: str, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict]):
        """Ajoute ou met à jour des items dans une collection vectorielle."""
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
    def get_catalog_by_type(self, media_type: str, limit: int = 1000, offset: int = 0) -> List[Dict]:
        """Récupère le catalogue complet depuis la source relationnelle avec pagination."""
        pass

    @abstractmethod
    def search_media_items(self, query: str, media_type: Optional[str] = None, limit: int = 10, offset: int = 0) -> List[Dict]:
        """Recherche textuelle dans le catalogue relationnel avec pagination."""
        pass

    @abstractmethod
    def load_latent_space(self, media_type: str, vibe_type: str) -> Optional[Dict]:
        """Charge les données de l'espace latent pour la visualisation."""
        pass

    @abstractmethod
    def sync_latent_space(self, media_type: str, vibe_type: str, data: List[Dict]) -> int:
        """Synchronise les données de l'espace latent vers le stockage robuste."""
        pass
