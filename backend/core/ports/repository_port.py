from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any

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
    def upsert_items(self, collection_name: str, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict], documents: Optional[List[str]] = None):
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
    def query_data_natural_language(self, query: str, llm_service: Optional[Any] = None) -> List[Dict]:
        """Interroge le catalogue en langage naturel (Text-to-SQL) et renvoie les résultats."""
        pass
