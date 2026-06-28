import datetime

from animetix_project.logging_config import get_logger
from dependency_injector.wiring import Provide, inject
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from animetix.api.dependencies import get_session_service

from ...containers import Container
from ...models import GameplaySession

logger = get_logger("animetix." + __name__)

# --- COVERTEST MODE ---


def _pick_cover(cover_test_service, is_daily):
    if is_daily:
        return cover_test_service.get_daily_cover(datetime.date.today())
    return cover_test_service.get_random_cover()


def _cover_payload(state, reveal=False):
    over = state["game_over"]
    return {
        "cover_url": state["url"],
        "locale": state["locale"],
        "volume": state["volume"],
        "author": state.get("author"),
        "guesses": state["guesses"],
        "game_over": over,
        "secret_title": state["secret"] if (over or reveal) else None,
    }


class CovertestTitlesView(APIView):
    """Manga titles for the guess autocomplete (same catalog used to validate)."""

    permission_classes = [permissions.AllowAny]

    @inject
    def get(self, request, catalog_service=Provide[Container.core.catalog_service]):
        data = catalog_service.load_data("Manga")
        titles = sorted((data or {}).get("title_to_full_data", {}).keys())
        return Response({"titles": titles})


class CovertestGameStateView(APIView):
    permission_classes = [permissions.AllowAny]

    @inject
    def get(
        self,
        request,
        cover_test_service=Provide[Container.core.cover_test_service],
    ):
        session_service = get_session_service(request)
        state = session_service.get_covertest_state()

        # Auto-start a round if none is in progress.
        if not state["secret"]:
            is_daily = request.query_params.get("is_daily", "false").lower() in (
                "true",
                "1",
            )
            cover = _pick_cover(cover_test_service, is_daily)
            if not cover:
                return Response(
                    {"error": "No game in progress and auto-start failed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            session_service.start_covertest_game(cover)
            session_service.port.set("covertest_is_daily", is_daily)
            state = session_service.get_covertest_state()

        return Response(_cover_payload(state))


class CovertestGameStartView(APIView):
    permission_classes = [permissions.AllowAny]

    @inject
    def post(
        self,
        request,
        cover_test_service=Provide[Container.core.cover_test_service],
    ):
        session_service = get_session_service(request)
        is_daily = bool(request.data.get("is_daily", False))

        cover = _pick_cover(cover_test_service, is_daily)
        if not cover:
            return Response(
                {"error": "Failed to select cover"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        session_service.start_covertest_game(cover)
        session_service.port.set("covertest_is_daily", is_daily)
        return Response(_cover_payload(session_service.get_covertest_state()))


class CovertestGameRevealView(APIView):
    """Ends the round and reveals the answer (used on loss / give-up)."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        session_service = get_session_service(request)
        state = session_service.get_covertest_state()
        if not state["secret"]:
            return Response(
                {"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST
            )
        session_service.port.set("covertest_game_over", True)
        state = session_service.get_covertest_state()
        return Response(_cover_payload(state, reveal=True))


class CovertestGameGuessView(APIView):
    permission_classes = [permissions.AllowAny]

    @inject
    def post(
        self,
        request,
        catalog_service=Provide[Container.core.catalog_service],
        game_service=Provide[Container.core.game_service],
    ):
        session_service = get_session_service(request)
        port = session_service.port
        state = session_service.get_covertest_state()

        if not state["secret"]:
            return Response(
                {"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST
            )
        if state["game_over"]:
            return Response(
                {"error": "Game already over"}, status=status.HTTP_400_BAD_REQUEST
            )

        guess_title = request.data.get("guess")
        if not guess_title:
            return Response(
                {"error": "Guess is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        data = catalog_service.load_data("Manga")
        secret = state["secret"]
        secret_item = (data or {}).get("title_to_full_data", {}).get(secret)
        is_correct = game_service.check_title_match(guess_title, secret_item)

        guess_full = (data or {}).get("title_to_full_data", {}).get(guess_title, {})
        image_url = (
            str(guess_full.get("image"))
            if guess_full and guess_full.get("image")
            else None
        )

        guesses = state["guesses"]
        guesses.append(
            {
                "title": str(guess_title),
                "image": image_url,
                "is_correct": bool(is_correct),
            }
        )
        port.set("covertest_guesses", guesses)

        unlocked_achievements = []
        if is_correct:
            port.set("covertest_game_over", True)
            if request.user.is_authenticated:
                try:
                    newly_unlocked = request.user.profile.add_win(
                        is_daily=port.get("covertest_is_daily", False),
                        game_mode="covertest",
                        media_type="Manga",
                        attempts=len(guesses),
                    )
                    for ach in newly_unlocked or []:
                        unlocked_achievements.append(
                            {
                                "name": ach.name,
                                "description": ach.description,
                                "xp_reward": ach.xp_reward,
                                "badge_url": getattr(ach, "badge_url", None),
                            }
                        )
                except Exception as e:
                    logger.warning(f"Handled error in CovertestGameGuessView: {e}")
            GameplaySession.objects.create(
                user=request.user if request.user.is_authenticated else None,
                game_mode="covertest",
                media_type="Manga",
                target_item=secret,
                history=guesses,
                was_won=True,
            )

        return Response(
            {
                "is_correct": is_correct,
                "guesses": guesses,
                "game_over": is_correct,
                "secret_title": secret if is_correct else None,
                "newly_unlocked_achievements": unlocked_achievements,
            }
        )
