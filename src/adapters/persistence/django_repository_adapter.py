from typing import List, Dict, Optional
from core.ports.repository_port import RepositoryPort
from animetix.models import MediaItem
from django.db.models import Q
from pgvector.django import CosineDistance

class DjangoRepositoryAdapter(RepositoryPort):
    def get_nearest_neighbors(self, collection_name: str, item_id: str, n_results: int = 5) -> List[Dict]:
        """Utilise CosineDistance pour trouver les voisins les plus proches."""
        try:
            item = MediaItem.objects.get(external_id=item_id)
            # Supposons que collection_name mappe vers un champ spécifique, ex: plot_embedding
            embedding_field = f"{collection_name.lower()}_embedding"
            if not hasattr(item, embedding_field): return []
            
            query_vec = getattr(item, embedding_field)
            if query_vec is None: return []

            # Recherche des voisins
            neighbors = MediaItem.objects.exclude(external_id=item_id).annotate(
                distance=CosineDistance(embedding_field, query_vec)
            ).order_by('distance')[:n_results]
            
            return [self._to_dict(n) for n in neighbors]
        except MediaItem.DoesNotExist:
            return []

    def load_catalog(self, media_type: str) -> Optional[Dict]:
        items = MediaItem.objects.filter(media_type=media_type)
        return {
            'lookup': [self._to_dict(item) for item in items],
            'title_to_full_data': {item.title: self._to_dict(item) for item in items}
        }

    def load_themes(self) -> Dict:
        # Implémentation basée sur l'agrégation des tags dans les métadonnées
        return {}

    def load_covers(self) -> Dict:
        return {}

    def calculate_similarity(self, collection_name: str, item_a_id: str, item_b_id: str) -> float:
        """Calcule la similarité cosinus entre deux items."""
        try:
            item_a = MediaItem.objects.get(external_id=item_a_id)
            item_b = MediaItem.objects.get(external_id=item_b_id)
            embedding_field = f"{collection_name.lower()}_embedding"
            
            vec_a = getattr(item_a, embedding_field)
            vec_b = getattr(item_b, embedding_field)
            
            if vec_a is None or vec_b is None: return 0.0
            
            # Similarité = 1 - Distance
            dist = MediaItem.objects.filter(id=item_a.id).annotate(
                d=CosineDistance(embedding_field, vec_b)
            ).first().d
            return 1.0 - dist
        except:
            return 0.0

    def upsert_items(self, collection_name: str, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict]):
        # Implémentation pour mise à jour par lots via bulk_create avec update_fields
        for i, external_id in enumerate(ids):
            item, _ = MediaItem.objects.update_or_create(
                external_id=external_id,
                defaults={f"{collection_name.lower()}_embedding": embeddings[i], "metadata": metadatas[i]}
            )

    def delete_collection(self, collection_name: str):
        # Réinitialisation des vecteurs d'une collection spécifique
        MediaItem.objects.all().update(**{f"{collection_name.lower()}_embedding": None})

    def get_collection_count(self, collection_name: str) -> int:
        return MediaItem.objects.exclude(**{f"{collection_name.lower()}_embedding": None}).count()

    def get_all_ids(self, collection_name: str) -> List[str]:
        return list(MediaItem.objects.exclude(**{f"{collection_name.lower()}_embedding": None}).values_list('external_id', flat=True))

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

    def load_latent_space(self, media_type: str, vibe_type: str) -> Optional[List[Dict]]:
        from animetix.models import LatentSpacePoint
        points = LatentSpacePoint.objects.filter(media_type=media_type.lower(), vibe_type=vibe_type.lower())
        if not points.exists():
            return None
        return [
            {
                'x': p.x, 'y': p.y, 'z': p.z,
                'title': p.title, 'external_id': p.external_id,
                'cluster': p.cluster, 'metadata': p.metadata
            } for p in points
        ]

    def sync_latent_space(self, media_type: str, vibe_type: str, data: List[Dict]) -> int:
        from animetix.models import LatentSpacePoint
        count = 0
        media_type = media_type.lower()
        vibe_type = vibe_type.lower()
        
        # Suppression des anciens points pour ce type
        LatentSpacePoint.objects.filter(media_type=media_type, vibe_type=vibe_type).delete()
        
        objs = []
        for d in data:
            objs.append(LatentSpacePoint(
                media_type=media_type,
                vibe_type=vibe_type,
                external_id=str(d.get('external_id') or d.get('id', '')),
                title=d.get('title') or d.get('name', 'Unknown'),
                x=d.get('x', 0.0),
                y=d.get('y', 0.0),
                z=d.get('z', 0.0),
                cluster=d.get('cluster', 0),
                metadata=d.get('metadata', {})
            ))
        
        created = LatentSpacePoint.objects.bulk_create(objs, batch_size=500)
        return len(created)

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
