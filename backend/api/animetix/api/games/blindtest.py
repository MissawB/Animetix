import datetime

from animetix_project.logging_config import get_logger
from dependency_injector.wiring import Provide, inject
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from animetix.api.dependencies import get_session_service

from ...containers import Container
from ...models import GameplaySession

logger = get_logger("animetix.games.blindtest")

# --- BLINDTEST MODE ---


class BlindtestGameStateView(APIView):
    permission_classes = [permissions.AllowAny]

    @inject
    def get(
        self, request, blind_test_service=Provide[Container.core.blind_test_service]
    ):
        session_service = get_session_service(request)
        port = session_service.port
        state = blind_test_service.get_state(port)
        if not state.secret:
            return Response(
                {"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "video_url": state.video,
                "theme_type": state.type,
                "blindtest_song": state.song,
                "blindtest_artists": state.artists,
                "guesses": state.guesses,
                "game_over": state.game_over,
                "is_daily": state.is_daily,
                "secret_title": state.secret if state.game_over else None,
            }
        )


class BlindtestGameStartView(APIView):
    permission_classes = [permissions.AllowAny]

    @inject
    def post(
        self,
        request,
        catalog_service=Provide[Container.core.catalog_service],
        blind_test_service=Provide[Container.core.blind_test_service],
    ):
        session_service = get_session_service(request)
        port = session_service.port
        media_type = "Anime"
        is_daily = request.data.get("is_daily", False)
        theme_pref = request.data.get("type")

        data = catalog_service.load_data(media_type)
        if not data:
            return Response(
                {"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if is_daily:
            theme = blind_test_service.get_daily_theme(datetime.date.today())
        else:
            theme = blind_test_service.get_random_theme(theme_type=theme_pref)

        if not theme:
            return Response(
                {"error": "Failed to select theme"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        state = blind_test_service.get_state(port)
        state.secret = theme["anime_title"]
        state.video = theme["video_url"]
        state.type = theme["type"]
        state.song = theme["song_title"]
        state.artists = theme["artists"]
        state.guesses = []
        state.game_over = False
        state.is_daily = is_daily

        blind_test_service.save_state(port, state)

        return Response(
            {
                "video_url": state.video,
                "theme_type": state.type,
                "blindtest_song": state.song,
                "blindtest_artists": state.artists,
                "guesses": [],
                "game_over": False,
                "is_daily": is_daily,
            }
        )


class BlindtestGameGuessView(APIView):
    permission_classes = [permissions.AllowAny]

    @inject
    def post(
        self,
        request,
        catalog_service=Provide[Container.core.catalog_service],
        blind_test_service=Provide[Container.core.blind_test_service],
        game_service=Provide[Container.core.game_service],
    ):
        session_service = get_session_service(request)
        port = session_service.port
        state = blind_test_service.get_state(port)

        if not state.secret:
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

        media_type = "Anime"
        data = catalog_service.load_data(media_type)
        secret = state.secret

        secret_item = data["title_to_full_data"].get(secret)
        is_correct = game_service.check_title_match(guess_title, secret_item)

        guess_full = data["title_to_full_data"].get(guess_title, {})
        image_url = (
            str(guess_full.get("image"))
            if guess_full and guess_full.get("image")
            else None
        )

        state.guesses.append(
            {
                "title": str(guess_title),
                "image": image_url,
                "is_correct": bool(is_correct),
            }
        )

        unlocked_achievements = []
        if is_correct:
            state.game_over = True
            if request.user.is_authenticated:
                try:
                    newly_unlocked = request.user.profile.add_win(
                        is_daily=state.is_daily,
                        game_mode="blindtest",
                        media_type=media_type,
                        attempts=len(state.guesses),
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
                    logger.warning(f"Handled error in BlindtestGameGuessView: {e}")
            GameplaySession.objects.create(
                user=request.user if request.user.is_authenticated else None,
                game_mode="blindtest",
                media_type=media_type,
                target_item=secret,
                history=state.guesses,
                was_won=True,
            )

        blind_test_service.save_state(port, state)

        return Response(
            {
                "is_correct": is_correct,
                "guesses": state.guesses,
                "game_over": is_correct,
                "secret_title": secret if is_correct else None,
                "newly_unlocked_achievements": unlocked_achievements,
            }
        )
