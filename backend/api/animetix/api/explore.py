from animetix_project.logging_config import get_logger
from dependency_injector.wiring import Provide, inject
from rest_framework import permissions, response, status, views

from ..containers import Container
from ..models import (
    MediaItem,
    UserRecommendation,
)

logger = get_logger("animetix.explore")


class MediaExploreView(views.APIView):
    """Explore le catalogue par popularité et catégories."""

    permission_classes = [permissions.AllowAny]

    @inject
    def get(self, request, catalog_service=Provide[Container.core.catalog_service]):
        media_type = request.query_params.get("media_type", "Anime")
        limit = int(request.query_params.get("limit", 20))

        try:
            catalog = catalog_service.get_catalog(media_type)
            items = catalog.get("db", [])[:limit]

            # 1. Recommandations personnalisées (IA)
            recommendations = []
            if request.user.is_authenticated:
                user_recs = (
                    UserRecommendation.objects.filter(
                        user=request.user, media_item__media_type=media_type
                    )
                    .select_related("media_item")
                    .order_by("rank")[:10]
                )

                recommendations = [
                    {
                        "id": rec.media_item.external_id,
                        "title": rec.media_item.title,
                        "image": rec.media_item.image_url,
                        "synopsis_fr": rec.media_item.synopsis_fr,
                        "is_recommendation": True,
                    }
                    for rec in user_recs
                ]

            # 2. Catégories populaires (ex: Action, Romance, etc.)
            categories = {}
            for item in catalog.get("db", []):
                genres = item.get("genres", [])
                for g in genres:
                    if g not in categories:
                        categories[g] = []
                    if len(categories[g]) < 10:
                        categories[g].append(item)

            return response.Response(
                {
                    "trending": items,
                    "recommendations": recommendations,
                    "categories": [
                        {"name": name, "items": items[:limit]}
                        for name, items in categories.items()
                        if len(items) >= 5
                    ][:10],
                }
            )

        except Exception:
            logger.exception("Error in MediaExploreView")
            return response.Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SeichijunreiMapView(views.APIView):
    """Récupère tous les lieux de pèlerinage réels pour la carte interactive (Seichijunrei)."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        locations = []
        try:
            # On récupère les médias ayant des lieux de pèlerinage dans leurs métadonnées
            # Supporté par Django JSONField (SQLite & Postgres)
            items = MediaItem.objects.filter(
                metadata__has_key="real_locations_pilgrimage"
            )

            for item in items:
                pilgrimage_data = item.metadata.get("real_locations_pilgrimage", [])
                if not isinstance(pilgrimage_data, list):
                    continue

                for loc in pilgrimage_data:
                    # On s'assure d'avoir au moins le nom et la ville (les coordonnées sont nouvelles)
                    locations.append(
                        {
                            "id": f"{item.external_id}_{hash(loc.get('location_name', ''))}",
                            "media_id": item.external_id,
                            "media_title": item.title,
                            "media_type": item.media_type,
                            "location_name": loc.get("location_name", "Lieu inconnu"),
                            "city": loc.get("city", ""),
                            "lat": loc.get("lat"),
                            "lng": loc.get("lng"),
                            "description": loc.get("scene_description", ""),
                            "image": item.image_url,
                        }
                    )

            return response.Response(locations)
        except Exception:
            logger.exception("Error in SeichijunreiMapView")
            return response.Response({"error": "Internal server error"}, status=500)


class MarketWikiView(views.APIView):
    """Expose les données du marché (éditeurs, diffuseurs) pour le Wiki."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            from backend.pipeline.mlops.french_market_db import (  # noqa: E402
                FRENCH_ANIME_DISTRIBUTORS,
                FRENCH_MANGA_PUBLISHERS,
            )
            from backend.pipeline.mlops.japanese_market_db import (  # noqa: E402
                JAPANESE_ANIME_DISTRIBUTORS,
                JAPANESE_MANGA_PUBLISHERS,
            )

            return response.Response(
                {
                    "japanese": {
                        "publishers": JAPANESE_MANGA_PUBLISHERS,
                        "distributors": JAPANESE_ANIME_DISTRIBUTORS,
                    },
                    "french": {
                        "publishers": FRENCH_MANGA_PUBLISHERS,
                        "distributors": FRENCH_ANIME_DISTRIBUTORS,
                    },
                }
            )
        except ImportError:
            # Fallback if path is different (depends on how it's executed)
            try:
                from pipeline.mlops.french_market_db import (  # noqa: E402
                    FRENCH_ANIME_DISTRIBUTORS,
                    FRENCH_MANGA_PUBLISHERS,
                )
                from pipeline.mlops.japanese_market_db import (  # noqa: E402
                    JAPANESE_ANIME_DISTRIBUTORS,
                    JAPANESE_MANGA_PUBLISHERS,
                )

                return response.Response(
                    {
                        "japanese": {
                            "publishers": JAPANESE_MANGA_PUBLISHERS,
                            "distributors": JAPANESE_ANIME_DISTRIBUTORS,
                        },
                        "french": {
                            "publishers": FRENCH_MANGA_PUBLISHERS,
                            "distributors": FRENCH_ANIME_DISTRIBUTORS,
                        },
                    }
                )
            except Exception as e:
                return response.Response(
                    {"error": f"Data not found: {str(e)}"}, status=404
                )
        except Exception:
            logger.exception("Error in MarketWikiView")
            return response.Response({"error": "Internal server error"}, status=500)


# MarketListingViewSet has been removed
