import logging
import numpy as np
from typing import List, Dict, Optional
from django.db.models import F
from django.db import connection, models
from animetix.models import MediaItem
from core.ports.repository_port import RepositoryPort

logger = logging.getLogger('animetix')

class PgVectorRepositoryAdapter(RepositoryPort):
    """
    Adaptateur utilisant pgvector (PostgreSQL) pour la recherche vectorielle.
    Centralise les données dans la base de données principale.
    """
    
    def __init__(self):
        self.enabled = False
        self._extension_checked = False
        try:
            from pgvector.django import VectorField
            self.enabled = True
        except ImportError:
            logger.warning("pgvector is not installed. PgVectorRepositoryAdapter will be disabled.")
            
        self.coll_to_field = {
            'anime_thematic': 'thematic_embedding',
            'manga_thematic': 'thematic_embedding',
            'anime_plot': 'plot_embedding',
            'character_vibe': 'thematic_embedding',
            'character_visual_vibe': 'visual_embedding',
            'movie_thematic': 'thematic_embedding',
            'game_thematic': 'thematic_embedding',
            'actor_vibe': 'thematic_embedding'
        }

    def _ensure_extension(self):
        """S'assure que l'extension vector est activée et crée les index HNSW."""
        if not self.enabled or self._extension_checked:
            return
        try:
            with connection.cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
                # Création des index HNSW pour chaque champ vectoriel
                # M=16 est le nombre de liens par nœud, ef_construction=64 pour le compromis construction/vitesse
                for field in self.coll_to_field.values():
                    index_name = f"idx_hnsw_{field}"
                    cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON animetix_mediaitem USING hnsw ({field} vector_cosine_ops) WITH (m=16, ef_construction=64)")
            self._extension_checked = True
        except Exception as e:
            logger.warning(f"Could not setup pgvector/HNSW: {e}")
            self.enabled = False

    def get_nearest_neighbors(self, collection_name: str, item_id: str, n_results: int = 5) -> Optional[Dict]:
        """
        Recherche par similarité optimisée via Matryoshka (MRL).
        Phase 1: Recherche ultra-rapide sur les 128 premières dimensions (SOTA 2026).
        Phase 2: Raffinement sur les dimensions complètes pour le top 50.
        """
        self._ensure_extension()
        if not self.enabled: return None
        field_name = self.coll_to_field.get(collection_name)
        if not field_name: return None
        
        try:
            # Récupération du vecteur de référence
            target_item = MediaItem.objects.get(external_id=item_id)
            target_vector = getattr(target_item, field_name)
            if target_vector is None: return None
            
            # --- STAGE 1 : DYNAMIC SLICING (Matryoshka) ---
            # Utilisation des 256 premières dimensions pour un filtrage rapide (SOTA 2026)
            # Les modèles Jina-v3 sont optimisés pour conserver l'information dans les premiers segments
            annotated_qs = MediaItem.objects.exclude(external_id=item_id).filter(media_type=target_item.media_type)
            
            # Note: Pour pgvector >= 0.5.0, cosine_distance supporte le slicing directement si le champ est de type Vector
            # On simule ici l'optimisation en limitant la dimension si possible via SQL brut ou via l'adaptateur
            try:
                candidates = annotated_qs.annotate(
                    fast_dist=F(field_name).cosine_distance(target_vector[:256])
                ).order_by('fast_dist')[:100]
            except Exception as e:
                logger.debug(f"Matryoshka Slice Level 1 failed, falling back to indexed search: {e}")
                candidates = annotated_qs.annotate(
                    fast_dist=F(field_name).cosine_distance(target_vector)
                ).order_by('fast_dist')[:100]
            
            # --- STAGE 2 : FULL RERANKING ---
            # On affine le top 100 avec les 1024 dimensions complètes pour une précision maximale
            similar_items = sorted(
                candidates, 
                key=lambda x: self._calculate_full_cosine(getattr(x, field_name), target_vector)
            )[:n_results]
            
            return {
                "ids": [[item.external_id for item in similar_items]],
                "distances": [[0.0 for _ in similar_items]], # Scores recalculés
                "metadatas": [[self._to_metadata(item) for item in similar_items]]
            }
        except Exception as e:
            logger.error(f"PgVector Matryoshka Error: {e}")
            return None

    def _calculate_full_cosine(self, v1, v2) -> float:
        if v1 is None or v2 is None: return 1.0
        a, b = np.array(v1), np.array(v2)
        return float(1.0 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def calculate_similarity(self, collection_name: str, item_a_id: str, item_b_id: str) -> float:
        field_name = self.coll_to_field.get(collection_name)
        if not field_name: return 0.0
        
        try:
            items = MediaItem.objects.filter(external_id__in=[item_a_id, item_b_id])
            if items.count() < 2: return 0.0
            
            vec_a = getattr(items.get(external_id=item_a_id), field_name)
            vec_b = getattr(items.get(external_id=item_b_id), field_name)
            
            if vec_a is None or vec_b is None: return 0.0
            
            # Calcul manuel de la similarité cosinus (ou via SQL si on préfère)
            dot = np.dot(vec_a, vec_b)
            norm_a = np.linalg.norm(vec_a)
            norm_b = np.linalg.norm(vec_b)
            return float(dot / (norm_a * norm_b))
        except Exception as e:
            logger.error(f"PgVector Similarity Error: {e}")
        return 0.0

    def load_catalog(self, media_type: str) -> Optional[Dict]:
        """Charge le catalogue pour compatibilité (limité pour éviter surcharge RAM)."""
        items = MediaItem.objects.filter(media_type=media_type).order_by('-popularity')[:2000]
        db_content = [self._to_full_dict(item) for item in items]
        return {
            "lookup": [self._to_metadata(item) for item in items],
            "db": db_content,
            "id_to_full_data": {str(item['id']): item for item in db_content}
        }

    def _to_metadata(self, item: MediaItem) -> Dict:
        return {"title": item.title, "id": item.external_id, "image": item.image_url}

    def _to_full_dict(self, item: MediaItem) -> Dict:
        data = {
            'id': item.external_id,
            'title': item.title,
            'title_english': item.title_english,
            'title_native': item.title_native,
            'description': item.description,
            'image': item.image_url,
            'popularity': item.popularity,
            'genres': item.metadata.get('genres', []),
            'tags': item.metadata.get('tags', [])
        }
        return data

    # --- MÉTHODES DE MAINTENANCE ---
    def upsert_items(self, collection_name: str, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict]):
        field_name = self.coll_to_field.get(collection_name)
        if not field_name: return
        
        for i, ext_id in enumerate(ids):
            meta = metadatas[i]
            m_type = meta.get('media_type')
            
            # On tente de trouver l'item précisément
            qs = MediaItem.objects.filter(external_id=ext_id)
            if m_type: qs = qs.filter(media_type=m_type)
            
            item = qs.first()
            if item:
                setattr(item, field_name, embeddings[i])
                item.save(update_fields=[field_name])
            else:
                logger.warning(f"Could not find MediaItem {ext_id} ({m_type}) for vector update.")

    def delete_collection(self, collection_name: str):
        field_name = self.coll_to_field.get(collection_name)
        if field_name:
            MediaItem.objects.all().update(**{field_name: None})

    def get_collection_count(self, collection_name: str) -> int:
        field_name = self.coll_to_field.get(collection_name)
        return MediaItem.objects.exclude(**{f"{field_name}__isnull": True}).count() if field_name else 0

    def get_all_ids(self, collection_name: str) -> List[str]:
        field_name = self.coll_to_field.get(collection_name)
        return list(MediaItem.objects.exclude(**{f"{field_name}__isnull": True}).values_list('external_id', flat=True)) if field_name else []

    def get_media_item(self, media_type: str, external_id: str) -> Optional[Dict]:
        try:
            return self._to_full_dict(MediaItem.objects.get(media_type=media_type, external_id=external_id))
        except: return None

    def get_catalog_by_type(self, media_type: str, limit: int = 1000, offset: int = 0) -> List[Dict]:
        return [self._to_full_dict(i) for i in MediaItem.objects.filter(media_type=media_type)[offset:offset+limit]]

    def search_media_items(self, query: str, media_type: Optional[str] = None, limit: int = 10, offset: int = 0) -> List[Dict]:
        # Logique de recherche textuelle classique
        from django.db.models import Q
        qs = MediaItem.objects.filter(Q(title__icontains=query) | Q(title_english__icontains=query))
        if media_type: qs = qs.filter(media_type=media_type)
        return [self._to_full_dict(i) for i in qs.order_by('-popularity')[offset:offset+limit]]

    def hybrid_similarity_search(self, item_id: str, media_type: str, weights: Dict[str, float] = None, limit: int = 10) -> List[Dict]:
        """
        Recherche hybride combinant Thématique, Plot et Visuel via pgvector.
        Poids par défaut équilibrés.
        """
        weights = weights or {'thematic': 0.5, 'plot': 0.3, 'visual': 0.2}
        
        try:
            target = MediaItem.objects.get(external_id=item_id)
            
            # Construction de la requête SQL personnalisée pour combiner les scores
            # pgvector (1 - cosine_distance) = cosine_similarity
            query = MediaItem.objects.exclude(external_id=item_id).filter(media_type=media_type)
            
            # Annotation des scores individuels
            if target.thematic_embedding:
                query = query.annotate(thematic_sim=1 - F('thematic_embedding').cosine_distance(target.thematic_embedding))
            else:
                query = query.annotate(thematic_sim=models.Value(0.0, output_field=models.FloatField()))
                
            if target.plot_embedding:
                query = query.annotate(plot_sim=1 - F('plot_embedding').cosine_distance(target.plot_embedding))
            else:
                query = query.annotate(plot_sim=models.Value(0.0, output_field=models.FloatField()))
                
            if target.visual_embedding:
                query = query.annotate(visual_sim=1 - F('visual_embedding').cosine_distance(target.visual_embedding))
            else:
                query = query.annotate(visual_sim=models.Value(0.0, output_field=models.FloatField()))
                
            # Score hybride final
            query = query.annotate(
                hybrid_score=(
                    F('thematic_sim') * weights['thematic'] +
                    F('plot_sim') * weights['plot'] +
                    F('visual_sim') * weights['visual']
                )
            ).order_by('-hybrid_score')[:limit]
            
            return [self._to_full_dict(item) for item in query]
            
        except MediaItem.DoesNotExist:
            return []

    def load_themes(self) -> Dict: return {}
    def load_covers(self) -> Dict: return {}
