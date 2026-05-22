import logging
from typing import List, Dict, Optional
from core.ports.repository_port import RepositoryPort
from .chroma_repository_adapter import ChromaRepositoryAdapter
from .django_repository_adapter import DjangoRepositoryAdapter

logger = logging.getLogger('animetix')

class UnifiedRepositoryAdapter(RepositoryPort):
    """
    Unified adapter focusing on ChromaDB for vector operations.
    Primary: ChromaDB (Local/Fast)
    Relational: Django ORM (PostgreSQL)
    """
    def __init__(self, chroma_db_path: str, project_root: str):
        self.project_root = project_root
        self.chroma = ChromaRepositoryAdapter(db_path=chroma_db_path, project_root=project_root)
        self.django = DjangoRepositoryAdapter()
        logger.info("Using ChromaDB as primary vector repository adapter.")

    def _get_primary(self) -> RepositoryPort:
        return self.chroma

    def get_nearest_neighbors(self, collection_name: str, item_id: str, n_results: int = 5) -> Optional[Dict]:
        """Recherche par similarité optimisée sur ChromaDB."""
        return self.chroma.get_nearest_neighbors(collection_name, item_id, n_results)

    def calculate_similarity(self, collection_name: str, item_a_id: str, item_b_id: str) -> float:
        return self.chroma.calculate_similarity(collection_name, item_a_id, item_b_id)

    def load_catalog(self, media_type: str) -> Optional[Dict]:
        return self.chroma.load_catalog(media_type)

    def load_themes(self) -> Dict:
        return self.django.load_themes()

    def load_covers(self) -> Dict:
        return self.django.load_covers()

    def get_media_item(self, media_type: str, external_id: str) -> Optional[Dict]:
        return self.django.get_media_item(media_type, external_id)

    def search_media_items(self, query: str, media_type: Optional[str] = None, limit: int = 10, offset: int = 0) -> List[Dict]:
        return self.django.search_media_items(query, media_type, limit, offset)

    def upsert_items(self, collection_name: str, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict]):
        self.chroma.upsert_items(collection_name, ids, embeddings, metadatas)

    def delete_collection(self, collection_name: str):
        self.chroma.delete_collection(collection_name)

    def get_collection_count(self, collection_name: str) -> int:
        return self.chroma.get_collection_count(collection_name)

    def get_all_ids(self, collection_name: str) -> List[str]:
        return self.chroma.get_all_ids(collection_name)

    def get_catalog_by_type(self, media_type: str, limit: int = 1000, offset: int = 0) -> List[Dict]:
        return self.django.get_catalog_by_type(media_type, limit, offset)
