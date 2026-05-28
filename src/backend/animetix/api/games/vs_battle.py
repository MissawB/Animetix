from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from ...containers import get_container
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def run_vs_battle(request):
    """
    Exécute un combat entre deux personnages.
    Attends un payload: { "char_a": "...", "char_a_franchise": "...", "char_b": "...", "char_b_franchise": "..." }
    """
    char_a = request.data.get('char_a')
    char_b = request.data.get('char_b')
    char_a_franchise = request.data.get('char_a_franchise')
    char_b_franchise = request.data.get('char_b_franchise')

    if not char_a or not char_b:
        return Response({"error": "Veuillez fournir char_a et char_b."}, status=status.HTTP_400_BAD_REQUEST)

    container = get_container()
    vs_service = container.core.vs_battle_service()

    try:
        result = vs_service.run_battle(
            char_a_name=char_a,
            char_b_name=char_b,
            char_a_franchise=char_a_franchise,
            char_b_franchise=char_b_franchise
        )

        return Response({
            "character_a": result.character_a.model_dump(),
            "character_b": result.character_b.model_dump(),
            "winner": result.winner,
            "verdict_summary": result.verdict_summary,
            "debate_history": [turn.model_dump() for turn in result.debate_history]
        })
    except ValueError as ve:
        logger.warning(f"VS Battle validation error: {ve}")
        return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"VS Battle internal error: {e}", exc_info=True)
        return Response({"error": "Erreur interne lors de la résolution du combat."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
