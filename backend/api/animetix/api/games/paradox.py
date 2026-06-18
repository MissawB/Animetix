import random

from animetix_project.logging_config import get_logger
from core.ports.usage_port import UsagePort
from dependency_injector.wiring import Provide, inject
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from animetix.api.dependencies import get_session_service

from ...containers import Container
from ...models import GameplaySession

logger = get_logger("animetix." + __name__)

# --- PARADOX MODE ---


class ParadoxGameStateView(APIView):
    permission_classes = [permissions.AllowAny]

    @inject
    def get(
        self,
        request,
        catalog_service=Provide[Container.core.catalog_service],
        paradox_service=Provide[Container.core.paradox_service],
    ):
        session_service = get_session_service(request)
        port = session_service.port
        state = paradox_service.get_state(port)
        if not state.answer:
            return Response(
                {"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST
            )

        media_type = state.media
        data = catalog_service.load_data(media_type)

        options = []
        for t in state.options:
            options.append(
                {
                    "title": t,
                    "image": (
                        data["title_to_full_data"].get(t, {}).get("image")
                        if data
                        else None
                    ),
                }
            )

        return Response(
            {
                "media_type": media_type,
                "scenario": state.scenario,
                "options": options,
                "game_over": state.game_over,
                "is_daily": state.is_daily,
            }
        )


class ParadoxGameStartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @inject
    def post(
        self,
        request,
        catalog_service=Provide[Container.core.catalog_service],
        paradox_service=Provide[Container.core.paradox_service],
        usage_port: UsagePort = Provide[Container.infrastructure.usage_port],
    ):
        session_service = get_session_service(request)
        port = session_service.port
        media_type = request.data.get("media_type", port.get("media_type", "Anime"))

        # Quota Check
        tier = getattr(request, "user_tier", "free")
        if not usage_port.check_quota(request.user.id, tier):
            return Response(
                {"error": "Daily AI quota exceeded."}, status=status.HTTP_403_FORBIDDEN
            )

        port.set("media_type", media_type)
        is_daily = request.data.get("is_daily", False)

        data = catalog_service.load_data(media_type)
        if not data:
            return Response(
                {"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND
            )

        secret_title = port.get("secret_title")
        res_prepare = paradox_service.prepare_challenge(data, is_daily, secret_title)
        if not res_prepare or len(res_prepare) < 3:
            return Response(
                {"error": "Failed to prepare paradox challenge"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        t1, t2, intruder = res_prepare
        language = port.get("language", "Français")

        res = paradox_service.generate_logic(
            media_type,
            data["title_to_full_data"][t1],
            data["title_to_full_data"][t2],
            data["title_to_full_data"][intruder],
            language,
        )

        # Log Usage
        usage_port.log_usage(
            engine="paradox-reasoning-engine", units=5, user_id=request.user.id
        )

        state = paradox_service.get_state(port)
        state.answer = intruder
        state.options = [t1, t2, intruder]
        random.shuffle(state.options)
        state.reasoning = res.reasoning
        state.scenario = res.scenario
        state.media = media_type
        state.is_daily = is_daily
        state.game_over = False

        paradox_service.save_state(port, state)

        options = []
        for t in state.options:
            options.append(
                {
                    "title": t,
                    "image": (
                        data["title_to_full_data"].get(t, {}).get("image")
                        if data
                        else None
                    ),
                }
            )

        return Response(
            {
                "status": "started",
                "media_type": media_type,
                "scenario": state.scenario,
                "options": options,
                "game_over": False,
                "is_daily": state.is_daily,
            }
        )


class ParadoxGameGuessView(APIView):
    permission_classes = [permissions.AllowAny]

    @inject
    def post(
        self,
        request,
        catalog_service=Provide[Container.core.catalog_service],
        paradox_service=Provide[Container.core.paradox_service],
    ):
        session_service = get_session_service(request)
        port = session_service.port
        state = paradox_service.get_state(port)

        if not state.answer:
            return Response(
                {"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST
            )

        if state.game_over:
            return Response(
                {"error": "Game already over"}, status=status.HTTP_400_BAD_REQUEST
            )

        guess_title = request.data.get("guess")
        if not guess_title:
            return Response(
                {"error": "Guess is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        choice = guess_title
        answer = state.answer
        is_correct = choice == answer

        state.game_over = True
        paradox_service.save_state(port, state)

        media_type = state.media
        data = catalog_service.load_data(media_type)

        unlocked_achievements = []
        if is_correct:
            if request.user.is_authenticated:
                try:
                    newly_unlocked = request.user.profile.add_win(
                        is_daily=state.is_daily,
                        game_mode="paradox",
                        media_type=media_type,
                        attempts=1,
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
                    logger.warning(f"Handled error: {e}")

            GameplaySession.objects.create(
                user=request.user if request.user.is_authenticated else None,
                game_mode="paradox",
                media_type=media_type,
                target_item=answer,
                history=[{"guess": choice, "is_correct": is_correct}],
                was_won=is_correct,
            )

        final_opts = []
        for t in state.options:
            final_opts.append(
                {
                    "title": t,
                    "is_intruder": (t == answer),
                    "is_user_choice": (t == choice),
                    "image": (
                        data["title_to_full_data"].get(t, {}).get("image")
                        if data
                        else None
                    ),
                }
            )

        return Response(
            {
                "media_type": media_type,
                "is_correct": is_correct,
                "answer": answer,
                "reasoning": state.reasoning,
                "final_options": final_opts,
                "newly_unlocked_achievements": unlocked_achievements,
            }
        )
