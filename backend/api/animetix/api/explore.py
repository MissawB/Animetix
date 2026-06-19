from animetix_project.logging_config import get_logger
from dependency_injector.wiring import Provide, inject
from django.db import transaction
from django.db.models import Q
from rest_framework import permissions, response, serializers, status, views, viewsets
from rest_framework.decorators import action

from ..containers import Container
from ..models import (
    MarketListing,
    MediaItem,
    UserRecommendation,
    WalletTransaction,
)
from ..serializers import MarketListingSerializer

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

        except Exception as e:
            logger.error(f"Error in MediaExploreView: {e}", exc_info=True)
            return response.Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
        except Exception as e:
            logger.error(f"Error in SeichijunreiMapView: {e}")
            return response.Response({"error": str(e)}, status=500)


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
        except Exception as e:
            return response.Response({"error": str(e)}, status=500)


class MarketListingViewSet(viewsets.ModelViewSet):
    queryset = MarketListing.objects.filter(is_active=True)
    serializer_class = MarketListingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_filter = self.request.query_params.get("user_filter", "active")
        if user_filter == "mine":
            qs = MarketListing.objects.filter(seller=self.request.user)
        elif user_filter == "purchases":
            qs = MarketListing.objects.filter(
                fusion__creator=self.request.user, is_active=False
            ).exclude(seller=self.request.user)
        else:
            qs = MarketListing.objects.filter(is_active=True)

        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(fusion__title_a__icontains=search)
                | Q(fusion__title_b__icontains=search)
                | Q(fusion__art_style__icontains=search)
            )

        sort_by = self.request.query_params.get("sort", "newest")
        if sort_by == "price_asc":
            qs = qs.order_by("price")
        elif sort_by == "price_desc":
            qs = qs.order_by("-price")
        else:
            qs = qs.order_by("-created_at")
        return qs

    def perform_create(self, serializer):
        fusion = serializer.validated_data["fusion"]
        if fusion.creator != self.request.user:
            raise serializers.ValidationError(
                "Vous n'êtes pas le créateur de cet actif."
            )

        if MarketListing.objects.filter(fusion=fusion, is_active=True).exists():
            raise serializers.ValidationError("Cet actif est déjà en vente.")

        serializer.save(seller=self.request.user, is_active=True)

    @action(detail=True, methods=["post"])
    def buy(self, request, pk=None):
        listing = self.get_object()
        buyer = request.user
        seller = listing.seller

        if buyer == seller:
            return response.Response(
                {"error": "Vous ne pouvez pas acheter votre propre actif."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        price = listing.price
        buyer_profile = buyer.profile
        seller_profile = seller.profile

        if buyer_profile.wallet_balance < price:
            return response.Response(
                {"error": "Solde Berrix insuffisant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            # Update balances
            buyer_profile.wallet_balance -= price
            buyer_profile.save()

            seller_profile.wallet_balance += price
            seller_profile.save()

            # Transfer ownership
            fusion = listing.fusion
            fusion.creator = buyer
            fusion.save()

            # Update ManyToMany collected_fusions
            buyer_profile.collected_fusions.add(fusion)
            seller_profile.collected_fusions.remove(fusion)

            # Record transactions
            WalletTransaction.objects.create(
                user=buyer,
                amount=-price,
                transaction_type="market_purchase",
                description=f"Achat de la Fusion #{fusion.id} ({fusion.title_a} x {fusion.title_b})",
            )
            WalletTransaction.objects.create(
                user=seller,
                amount=price,
                transaction_type="market_sale",
                description=f"Vente de la Fusion #{fusion.id} ({fusion.title_a} x {fusion.title_b})",
            )

            # Mark listing inactive
            listing.is_active = False
            listing.save()

        return response.Response(
            {"status": "success", "message": "Achat effectué avec succès."}
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        listing = self.get_object()
        if listing.seller != request.user:
            return response.Response(
                {"error": "Vous n'êtes pas le vendeur de cet actif."},
                status=status.HTTP_403_FORBIDDEN,
            )
        listing.is_active = False
        listing.save()
        return response.Response({"status": "success", "message": "Vente annulée."})
