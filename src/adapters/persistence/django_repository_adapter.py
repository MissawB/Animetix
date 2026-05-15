from typing import List, Dict, Optional
from core.ports.repository_port import RepositoryPort
from animetix.models import MediaItem
from django.db.models import Q

class DjangoRepositoryAdapter(RepositoryPort):
    def get_nearest_neighbors(self, collection_name: str, item_id: str, n_results: int = 5) -> Optional[Dict]:
        return None

    def load_catalog(self, media_type: str) -> Optional[Dict]:
        return None

    def load_themes(self) -> Dict:
        return {}

    def load_covers(self) -> Dict:
        return {}

    def calculate_similarity(self, collection_name: str, item_a_id: str, item_b_id: str) -> float:
        return 0.0

    def upsert_items(self, collection_name: str, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict]):
        pass

    def delete_collection(self, collection_name: str):
        pass

    def get_collection_count(self, collection_name: str) -> int:
        return 0

    def get_all_ids(self, collection_name: str) -> List[str]:
        return []

    def get_media_item(self, media_type: str, external_id: str) -> Optional[Dict]:
        try:
            item = MediaItem.objects.get(media_type=media_type, external_id=external_id)
            return self._to_dict(item)
        except MediaItem.DoesNotExist:
            return None

    def get_catalog_by_type(self, media_type: str, limit: int = 2000, offset: int = 0) -> List[Dict]:
        items = MediaItem.objects.filter(media_type=media_type).order_by('-popularity')[offset:offset+limit]
        return [self._to_dict(item) for item in items]

    def search_media_items(self, query: str, media_type: Optional[str] = None, limit: int = 10, offset: int = 0) -> List[Dict]:
        qs = MediaItem.objects.filter(
            Q(title__icontains=query) | 
            Q(title_english__icontains=query) | 
            Q(title_native__icontains=query)
        )
        if media_type:
            qs = qs.filter(media_type=media_type)
        
        items = qs.order_by('-popularity')[offset:offset+limit]
        return [self._to_dict(item) for item in items]

    def _to_dict(self, item: MediaItem) -> Dict:
        data = {
            'id': item.external_id,
            'title': item.title,
            'title_english': item.title_english,
            'title_native': item.title_native,
            'description': item.description,
            'synopsis_en': item.synopsis_en,
            'synopsis_fr': item.synopsis_fr,
            'alternative_titles': item.alternative_titles,
            'image': item.image_url,
            'year': item.release_year,
            'popularity': item.popularity,
            'rating': item.rating
        }
        if item.metadata:
            data.update(item.metadata)
        return data
