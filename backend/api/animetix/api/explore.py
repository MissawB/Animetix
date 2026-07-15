from animetix_project.logging_config import get_logger
from dependency_injector.wiring import Provide, inject
from rest_framework import permissions, response, status, views

from ..containers import Container
from ..models import MediaItem

logger = get_logger("animetix.explore")


class MediaExploreView(views.APIView):
    """Feed personnalisé IA de la page Explorer (cascade de fallback)."""

    permission_classes = [permissions.AllowAny]

    @inject
    def get(self, request, feed_composer=Provide[Container.core.feed_composer]):
        media_type = request.query_params.get("media_type", "Anime")
        try:
            feed = feed_composer.compose(request.user, media_type)
            return response.Response(feed)
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
