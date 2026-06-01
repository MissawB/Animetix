from rest_framework import views, response, status, permissions
from ..containers import Container
from dependency_injector.wiring import inject, Provide
from ..serializers import MediaItemSerializer
from ..models import MediaItem
import logging

logger = logging.getLogger('animetix')

class MediaExploreView(views.APIView):
    """Explore le catalogue par popularité et catégories."""
    permission_classes = [permissions.AllowAny]

    @inject
    def get(self, request, catalog_service = Provide[Container.core.catalog_service]):
        media_type = request.query_params.get('media_type', 'Anime')
        limit = int(request.query_params.get('limit', 20))
        
        try:
            catalog = catalog_service.get_catalog(media_type)
            items = catalog.get('db', [])[:limit]
            
            # Catégories populaires (ex: Action, Romance, etc.)
            # On extrait ça des métadonnées des items chargés
            categories = {}
            for item in catalog.get('db', []):
                genres = item.get('genres', [])
                for g in genres:
                    if g not in categories:
                        categories[g] = []
                    if len(categories[g]) < 10:
                        categories[g].append(item)
            
            return response.Response({
                "trending": items,
                "categories": [
                    {"name": name, "items": items[:limit]} 
                    for name, items in categories.items() 
                    if len(items) >= 5
                ][:10]
            })
        except Exception as e:
            logger.error(f"Error in MediaExploreView: {e}", exc_info=True)
            return response.Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
