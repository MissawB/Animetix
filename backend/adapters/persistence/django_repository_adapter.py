import logging
from typing import Dict, List, Optional

from animetix.models import MediaItem
from core.ports.repository_port import RepositoryPort
from django.db.models import Q

logger = logging.getLogger("animetix")


class DjangoRepositoryAdapter(RepositoryPort):
    def get_nearest_neighbors(
        self, collection_name: str, item_id: str, n_results: int = 5
    ) -> Optional[Dict]:
        """Désactivé dans l'adaptateur relationnel. Utiliser pgvector."""
        return None

    def load_catalog(self, media_type: str) -> Optional[Dict]:
        items = MediaItem.objects.filter(media_type=media_type)
        return {
            "lookup": [self._to_dict(item) for item in items],
            "title_to_full_data": {item.title: self._to_dict(item) for item in items},
        }

    def load_themes(self) -> Dict:
        return {}

    def load_covers(self) -> Dict:
        return {}

    def calculate_similarity(
        self, collection_name: str, item_a_id: str, item_b_id: str
    ) -> float:
        """Désactivé dans l'adaptateur relationnel. Utiliser pgvector."""
        return 0.0

    def upsert_items(
        self,
        collection_name: str,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict],
        documents: Optional[List[str]] = None,
        strict: bool = False,
    ):
        """Upsert les items dans Django (ignore les embeddings).

        Rien n'est avalé ici : `strict` n'a rien à changer, l'échec lève déjà.
        """
        for i, external_id in enumerate(ids):
            MediaItem.objects.update_or_create(
                external_id=external_id, defaults={"metadata": metadatas[i]}
            )

    def delete_collection(self, collection_name: str):
        """Désactivé."""
        pass

    def get_collection_count(self, collection_name: str) -> int:
        """Désactivé."""
        return 0

    def get_all_ids(self, collection_name: str) -> List[str]:
        """Désactivé."""
        return []

    def get_media_item(self, media_type: str, external_id: str) -> Optional[Dict]:
        try:
            item = MediaItem.objects.get(media_type=media_type, external_id=external_id)
            return self._to_dict(item)
        except MediaItem.DoesNotExist:
            return None

    def get_catalog_by_type(
        self, media_type: str, limit: int = 2000, offset: int = 0
    ) -> List[Dict]:
        items = MediaItem.objects.filter(media_type=media_type).order_by("-popularity")[
            offset : offset + limit
        ]
        return [self._to_dict(item) for item in items]

    def search_media_items(
        self,
        query: str,
        media_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict]:
        qs = MediaItem.objects.filter(
            Q(title__icontains=query)
            | Q(title_english__icontains=query)
            | Q(title_native__icontains=query)
        )
        if media_type:
            qs = qs.filter(media_type=media_type)

        items = qs.order_by("-popularity")[offset : offset + limit]
        return [self._to_dict(item) for item in items]

    def load_latent_space(
        self, media_type: str, vibe_type: str
    ) -> Optional[List[Dict]]:
        from animetix.models import LatentSpacePoint  # noqa: E402

        points = LatentSpacePoint.objects.filter(
            media_type=media_type.lower(), vibe_type=vibe_type.lower()
        )
        if not points.exists():
            return None
        return [
            {
                "x": p.x,
                "y": p.y,
                "z": p.z,
                "title": p.title,
                "external_id": p.external_id,
                "cluster": p.cluster,
                "metadata": p.metadata,
            }
            for p in points
        ]

    def sync_latent_space(
        self, media_type: str, vibe_type: str, data: List[Dict]
    ) -> int:
        from animetix.models import LatentSpacePoint  # noqa: E402

        media_type = media_type.lower()
        vibe_type = vibe_type.lower()

        LatentSpacePoint.objects.filter(
            media_type=media_type, vibe_type=vibe_type
        ).delete()

        objs = []
        for d in data:
            objs.append(
                LatentSpacePoint(
                    media_type=media_type,
                    vibe_type=vibe_type,
                    external_id=str(d.get("external_id") or d.get("id", "")),
                    title=d.get("title") or d.get("name", "Unknown"),
                    x=d.get("x", 0.0),
                    y=d.get("y", 0.0),
                    z=d.get("z", 0.0),
                    cluster=d.get("cluster", 0),
                    metadata=d.get("metadata", {}),
                )
            )

        created = LatentSpacePoint.objects.bulk_create(objs, batch_size=500)
        return len(created)

    def get_creative_fusion(self, fusion_id: int) -> Optional[Dict]:
        from animetix.models import CreativeFusion  # noqa: E402

        try:
            fusion = CreativeFusion.objects.get(id=fusion_id)
            return {
                "id": fusion.id,
                "title_a": fusion.title_a,
                "title_b": fusion.title_b,
                "scenario": fusion.scenario_text,
                "image": fusion.image_url,
                "art_style": fusion.art_style,
            }
        except CreativeFusion.DoesNotExist:
            # Narrow: only "not found" maps to None; real DB errors must surface.
            return None

    def get_user_gameplay_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        from animetix.models import GameplaySession  # noqa: E402

        sessions = GameplaySession.objects.filter(user_id=user_id).order_by(
            "-created_at"
        )[:limit]
        return [
            {"target": s.target_item, "media_type": s.media_type, "won": s.was_won}
            for s in sessions
        ]

    def get_user_creative_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        from animetix.models import CreativeFusion  # noqa: E402

        fusions = CreativeFusion.objects.filter(creator_id=user_id).order_by(
            "-created_at"
        )[:limit]
        return [
            {"art_style": f.art_style, "titles": f"{f.title_a} x {f.title_b}"}
            for f in fusions
        ]

    def _to_dict(self, item: MediaItem) -> Dict:
        data = {
            "id": item.external_id,
            "title": item.title,
            "media_type": item.media_type,
            "title_english": item.title_english,
            "title_native": item.title_native,
            "description": item.description,
            "synopsis_en": item.synopsis_en,
            "synopsis_fr": item.synopsis_fr,
            "alternative_titles": item.alternative_titles,
            "image": item.image_url,
            "year": item.release_year,
            "popularity": item.popularity,
            "rating": item.rating,
        }
        if item.metadata:
            data.update(item.metadata)
        return data
