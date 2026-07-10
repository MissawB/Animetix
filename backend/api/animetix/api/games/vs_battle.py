import logging

from core.domain.services.berrix_economy import FEATURE_BX_COSTS
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from animetix.api.billing import deduct_berrix

from ...containers import get_container
from ...models import MediaItem, VsBattle
from ...serializers import VsBattleResultSerializer, VsBattleSerializer

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny])
def list_vs_battles(request):
    """Liste les combats publics récents pour l'Arène."""
    battles = (
        VsBattle.objects.filter(is_public=True)
        .select_related("creator")
        .prefetch_related("likes")
        .order_by("-created_at")[:20]
    )
    serializer = VsBattleSerializer(battles, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def list_vs_characters(request):
    """Personnages sélectionnables (nom, franchise, image) pour l'Arène.

    Sert la galerie de sélection : le front filtre par nom ou par franchise.
    Trié par popularité réelle (``metadata.favourites``) car la colonne
    ``popularity`` n'est pas renseignée pour les personnages — sinon les
    personnages emblématiques (Goku, etc.) seraient hors de la sélection.
    """
    from django.db.models import F, IntegerField
    from django.db.models.fields.json import KeyTextTransform, KeyTransform
    from django.db.models.functions import Cast

    # `favourites` is nested at metadata -> popularity -> favourites.
    fav = Cast(
        KeyTextTransform("favourites", KeyTransform("popularity", "metadata")),
        IntegerField(),
    )
    base = (
        MediaItem.objects.filter(media_type="Character")
        .exclude(image_url__isnull=True)
        .exclude(image_url="")
        .annotate(fav=fav)
        .order_by(F("fav").desc(nulls_last=True))
    )

    # Once the roster has been precomputed (`precompute_vsbattle_sheets`), only
    # tagged characters — those with a VS Battles sheet, wiki or synthetic — are
    # offered. Until then, fall back to the most popular so the roster still works.
    tagged = base.filter(metadata__vsbattle__in_roster=True)
    qs = tagged if tagged.exists() else base[:2000]

    characters = [
        {
            "name": m.title,
            "franchise": (m.metadata or {}).get("origin") or "",
            "image": m.image_url,
            "source": ((m.metadata or {}).get("vsbattle") or {}).get("source")
            or "wiki",
        }
        for m in qs
    ]
    return Response({"characters": characters})


@extend_schema(responses=VsBattleResultSerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@ratelimit(key="user", rate="1/m", block=True)
def run_vs_battle(request):
    """
    Exécute un combat entre deux personnages et l'enregistre.
    Sécurisé par authentification, rate-limit et quotas.
    """
    char_a = request.data.get("char_a")
    char_b = request.data.get("char_b")
    char_a_franchise = request.data.get("char_a_franchise")
    char_b_franchise = request.data.get("char_b_franchise")

    if not char_a or not char_b:
        return Response(
            {"error": "Veuillez fournir char_a et char_b."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    container = get_container()
    vs_service = container.core.vs_battle_service()
    usage_port = container.infrastructure.usage_port()

    # Quota Check (Inférence coûteuse)
    tier = getattr(request, "user_tier", "free")
    if not usage_port.check_quota(request.user.id, tier):
        return Response(
            {"error": "Quota d'IA journalier atteint. Revenez demain !"},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Berrix deduction for the GPU battle reasoning (raises 402 if balance too low).
    # Kept outside the try below so PaymentRequired propagates as 402, not 500.
    deduct_berrix(
        request.user,
        FEATURE_BX_COSTS["vs_battle"],
        "Arène — combat IA",
    )

    try:
        result = vs_service.run_battle(
            char_a_name=char_a,
            char_b_name=char_b,
            char_a_franchise=char_a_franchise,
            char_b_franchise=char_b_franchise,
        )

        # Enregistrement dans la base de données
        battle_record = VsBattle.objects.create(
            char_a_name=char_a,
            char_b_name=char_b,
            char_a_franchise=char_a_franchise,
            char_b_franchise=char_b_franchise,
            char_a_data=result.character_a.model_dump(),
            char_b_data=result.character_b.model_dump(),
            winner=result.winner,
            verdict_summary=result.verdict_summary,
            debate_history=[turn.model_dump() for turn in result.debate_history],
            creator=request.user,
        )

        # Log usage (10 unités par combat Arena)
        usage_port.log_usage(
            engine="arena-vs-battle", units=10, user_id=request.user.id
        )

        return Response(
            {
                "id": battle_record.id,
                "character_a": result.character_a.model_dump(),
                "character_b": result.character_b.model_dump(),
                "winner": result.winner,
                "verdict_summary": result.verdict_summary,
                "debate_history": [turn.model_dump() for turn in result.debate_history],
            }
        )
    except ValueError as ve:
        logger.warning(f"VS Battle validation error: {ve}")
        return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"VS Battle internal error: {e}", exc_info=True)
        return Response(
            {"error": "Erreur interne lors de la résolution du combat."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def like_vs_battle(request, battle_id):
    """Aime un combat dans l'Arène."""
    try:
        battle = VsBattle.objects.get(id=battle_id)
        if request.user in battle.likes.all():
            battle.likes.remove(request.user)
            liked = False
        else:
            battle.likes.add(request.user)
            liked = True
        return Response(
            {"status": "success", "liked": liked, "likes_count": battle.likes.count()}
        )
    except VsBattle.DoesNotExist:
        return Response(
            {"error": "Combat non trouvé"}, status=status.HTTP_404_NOT_FOUND
        )
