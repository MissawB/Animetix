from animetix_project.logging_config import get_logger  # noqa: E402
from dependency_injector.wiring import Provide, inject
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.response import Response

from animetix.api.dependencies import get_session_service  # noqa: E402

from ...containers import Container  # noqa: E402
from ...models import GameplaySession  # noqa: E402
from .base import CpuGameAPIView

logger = get_logger("animetix." + __name__)

from ...serializers import (  # noqa: E402
    AkinetixAnswerSerializer,
    AkinetixConfirmSerializer,
    AkinetixStartSerializer,
)

# ... (rest of imports unchanged)

# --- AKINETIX MODE ---


class AkinetixGameStateView(CpuGameAPIView):
    @inject
    def get(self, request, akinetix_service=Provide[Container.core.akinetix_service]):
        session_service = get_session_service(request)
        port = session_service.port
        state = akinetix_service.get_state(port)
        if not state.current_q:
            return Response(
                {"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "media_type": port.get("media_type", "Anime"),
                "current_question": state.current_q,
                "history": [
                    q.model_dump() if hasattr(q, "model_dump") else q
                    for q in state.history
                ],
                "game_over": state.game_over,
                "ai_guess": state.ai_guess,
                "is_daily": state.is_daily,
                "confidence": state.confidence,
            }
        )


@method_decorator(
    ratelimit(key="user_or_ip", rate="60/m", method="POST", block=True), name="post"
)
class AkinetixGameStartView(CpuGameAPIView):
    @inject
    def post(
        self,
        request,
        catalog_service=Provide[Container.core.catalog_service],
        akinetix_service=Provide[Container.core.akinetix_service],
    ):
        serializer = AkinetixStartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        session_service = get_session_service(request)
        port = session_service.port
        media_type = data["media_type"]
        port.set("media_type", media_type)
        is_daily = data["is_daily"]
        difficulty = request.data.get("difficulty", "Normal")
        # The answer view must re-apply the same difficulty slice: the state's
        # probability vector is sized on the sliced pool at start.
        port.set("akinetix_difficulty", difficulty)

        cat_data = catalog_service.load_data(media_type)
        if not cat_data:
            return Response(
                {"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Difficulty bounds the candidate pool to the top-N most popular works
        # (Easy = famous, Impossible = whole catalogue). Catalogue is pop-sorted.
        from ...services import AKINETIX_DIFFICULTY_RANK  # noqa: E402

        limit = AKINETIX_DIFFICULTY_RANK.get(difficulty)
        db = cat_data["db"][:limit] if limit else cat_data["db"]

        game_state = akinetix_service.start_new_game(db)
        if is_daily:
            game_state.is_daily = True

        akinetix_service.save_state(port, game_state)

        return Response(
            {
                "status": "started",
                "media_type": media_type,
                "current_question": game_state.current_q,
                "history": [
                    q.model_dump() if hasattr(q, "model_dump") else q
                    for q in game_state.history
                ],
                "game_over": game_state.game_over,
                "ai_guess": game_state.ai_guess,
                "is_daily": game_state.is_daily,
                "confidence": game_state.confidence,
            }
        )


@method_decorator(
    ratelimit(key="user_or_ip", rate="60/m", method="POST", block=True), name="post"
)
class AkinetixGameAnswerView(CpuGameAPIView):
    @inject
    def post(
        self,
        request,
        catalog_service=Provide[Container.core.catalog_service],
        akinetix_service=Provide[Container.core.akinetix_service],
    ):
        session_service = get_session_service(request)
        port = session_service.port
        state = akinetix_service.get_state(port)
        if not state.current_q:
            return Response(
                {"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST
            )

        if state.game_over:
            return Response(
                {"error": "Game already over"}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AkinetixAnswerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        answer = serializer.validated_data["answer"]
        media_type = port.get("media_type", "Anime")
        cat_data = catalog_service.load_data(media_type)
        if not cat_data:
            return Response(
                {"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Same difficulty slice as at start: state.probs is sized on that pool.
        from ...services import AKINETIX_DIFFICULTY_RANK  # noqa: E402

        limit = AKINETIX_DIFFICULTY_RANK.get(port.get("akinetix_difficulty", ""))
        db = cat_data["db"][:limit] if limit else cat_data["db"]

        new_state = akinetix_service.process_answer(db, state, answer)
        akinetix_service.save_state(port, new_state)

        return Response(
            {
                "media_type": media_type,
                "current_question": new_state.current_q,
                "history": [
                    q.model_dump() if hasattr(q, "model_dump") else q
                    for q in new_state.history
                ],
                "game_over": new_state.game_over,
                "ai_guess": new_state.ai_guess,
                "is_daily": new_state.is_daily,
                "confidence": new_state.confidence,
            }
        )


@method_decorator(
    ratelimit(key="user", rate="2/m", method="POST", block=True), name="dispatch"
)
class AkinetixGameConfirmView(CpuGameAPIView):
    @inject
    def post(self, request, akinetix_service=Provide[Container.core.akinetix_service]):
        session_service = get_session_service(request)
        port = session_service.port
        state = akinetix_service.get_state(port)

        if not state.current_q and not state.ai_guess:
            return Response(
                {"error": "No game in progress to confirm"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AkinetixConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        is_correct = serializer.validated_data["correct"]
        media_type = port.get("media_type", "Anime")
        unlocked_achievements = []

        # --- ANTI-CHEAT VALIDATION ---
        if not is_correct:
            actual_target = serializer.validated_data.get("actual_target")
            if not actual_target:
                return Response(
                    {
                        "error": "You must specify the character you were thinking of to claim a victory."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Simple normalization for comparison
            normalized_guess = (state.ai_guess or "").lower().strip()
            normalized_actual = str(actual_target).lower().strip()

            if normalized_actual == normalized_guess:
                logger.warning(
                    f"🚩 Potential cheat detected: User {request.user} claimed AI was wrong, but provided the same target: {normalized_guess}"
                )
                return Response(
                    {
                        "error": "Cheat detected: The character you provided is the same as the AI guess!",
                        "is_cheat": True,
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Award XP only if validation passes
            if request.user.is_authenticated:
                try:
                    newly_unlocked = request.user.profile.add_win(
                        is_daily=state.is_daily,
                        game_mode="akinetix",
                        media_type=media_type,
                    )
                    if newly_unlocked:
                        for ach in newly_unlocked:
                            unlocked_achievements.append(
                                {
                                    "name": ach.name,
                                    "description": ach.description,
                                    "xp_reward": ach.xp_reward,
                                    "badge_url": (
                                        ach.badge_url
                                        if hasattr(ach, "badge_url")
                                        else None
                                    ),
                                }
                            )
                except Exception as e:
                    logger.error(
                        f"Error updating profile in Akinetix confirm: {e}",
                        exc_info=True,
                    )

        GameplaySession.objects.create(
            user=request.user if request.user.is_authenticated else None,
            game_mode="akinetix",
            media_type=media_type,
            target_item=serializer.validated_data.get(
                "actual_target", state.ai_guess or "Unknown"
            ),
            history=[
                q.model_dump() if hasattr(q, "model_dump") else q for q in state.history
            ],
            was_won=is_correct,
        )

        # Reset the Akinetix session state
        akinetix_service.reset_state(port)

        return Response(
            {
                "status": "confirmed",
                "was_won": is_correct,
                "user_won": not is_correct,
                "newly_unlocked_achievements": unlocked_achievements,
            }
        )
