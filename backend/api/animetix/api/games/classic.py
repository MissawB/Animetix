from animetix_project.logging_config import get_logger
from dependency_injector.wiring import Provide, inject
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from animetix.api.dependencies import get_session_service

from ...containers import Container
from ...models import GameplaySession

logger = get_logger("animetix." + __name__)

# --- CLASSIC MODE ---


class ClassicGameStateView(APIView):
    permission_classes = [permissions.AllowAny]

    @inject
    def get(self, request, catalog_service=Provide[Container.core.catalog_service]):
        session_service = get_session_service(request)
        state = session_service.get_classic_state()

        media_type = state["media_type"]
        secret_title = state["secret_title"]
        if not secret_title:
            return Response(
                {"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST
            )

        data = catalog_service.get_catalog(media_type)
        if not data:
            return Response(
                {"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND
            )

        secret_data = data["title_to_full_data"].get(secret_title)
        if not secret_data:
            return Response(
                {"error": "Secret title data not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        from ...presenters import GamePresenter  # noqa: E402

        hints = GamePresenter.format_classic_hints(
            secret_data, len(state["guesses"]), state["revealed_hints"]
        )

        return Response(
            {
                "media_type": media_type,
                "mediaType": media_type,
                "difficulty": state["difficulty"],
                "is_daily": state["is_daily"],
                "isDaily": state["is_daily"],
                "is_ranked": state["is_ranked"],
                "game_over": state["game_over"],
                "gameOver": state["game_over"],
                "guess_count": len(state["guesses"]),
                "guesses": state["guesses"],
                "hints": hints,
                "secret_title": secret_title if state["game_over"] else None,
                "secret_data": secret_data if state["game_over"] else None,
            }
        )


class ClassicGameStartView(APIView):
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
        media_type = request.data.get("media_type", "Anime")
        difficulty = request.data.get("difficulty", "Normal")
        override_secret = request.data.get("override_secret")

        port.update({"media_type": media_type, "difficulty": difficulty})

        data = catalog_service.get_catalog(media_type)
        if not data:
            return Response(
                {"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if override_secret and getattr(request.user, "is_staff", False):
            secret_title = override_secret
        else:
            if override_secret:
                logger.warning(
                    f"User {request.user} tried to override secret without staff permissions."
                )
            port.update({"is_daily": False, "is_ranked": False})
            from ...services import DIFFICULTY_SETTINGS  # noqa: E402

            secret_title = game_service.select_secret(
                media_type, difficulty, DIFFICULTY_SETTINGS
            )

        if not secret_title:
            return Response(
                {"error": "Failed to select secret title"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        port.update(
            {
                "secret_title": secret_title,
                "max_raw_sim": 0.8,
                "difficulty": difficulty,
                "media_type": media_type,
                "guesses": [],
                "game_over": False,
                "revealed_hints": [],
            }
        )

        return Response(
            {
                "status": "started",
                "media_type": media_type,
                "mediaType": media_type,
                "difficulty": difficulty,
                "is_daily": False,
                "isDaily": False,
                "is_ranked": False,
                "game_over": False,
                "gameOver": False,
                "guess_count": 0,
                "guesses": [],
            }
        )


class ClassicGameGuessView(APIView):
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
        state = {
            "secret_title": port.get("secret_title"),
            "guesses": port.get("guesses", []),
            "game_over": port.get("game_over", False),
            "media_type": port.get("media_type", "Anime"),
            "is_daily": port.get("is_daily", False),
            "is_ranked": port.get("is_ranked", False),
            "revealed_hints": port.get("revealed_hints", []),
        }
        if not state["secret_title"]:
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

        media_type = state["media_type"]
        secret_title = state["secret_title"]
        max_sim = port.get("max_raw_sim", 1.0)

        data = catalog_service.get_catalog(media_type)
        if not data or guess_title not in data["title_to_index"]:
            return Response(
                {"error": f"Title '{guess_title}' not in catalog"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_sim = game_service.calculate_raw_similarity(
            media_type, secret_title, guess_title, data
        )
        secret_item = data["title_to_full_data"].get(secret_title)
        is_correct = game_service.check_title_match(guess_title, secret_item)

        from ...presenters import GamePresenter  # noqa: E402

        score = (
            100.0
            if is_correct
            else round(min(0.99, (raw_sim / max_sim) * 0.99) * 100, 2)
        )
        color = GamePresenter.get_score_color(score)

        g_data = data["title_to_full_data"].get(guess_title, {})
        new_guess = {
            "title": guess_title,
            "title_english": g_data.get("title_english"),
            "title_native": g_data.get("title_native"),
            "image": g_data.get("image"),
            "score": score,
            "color": color,
            "is_correct": is_correct,
            "isCorrect": is_correct,
        }

        # Add guess
        guesses = port.get("guesses", [])
        guesses.append(new_guess)
        guesses.sort(key=lambda x: x["score"], reverse=True)
        port.set("guesses", guesses)

        unlocked_achievements = []
        if is_correct:
            port.set("game_over", True)
            if request.user.is_authenticated:
                item_rank = 100
                for i, item in enumerate(data["lookup"]):
                    if (item.get("title") or item.get("name")) == secret_title:
                        item_rank = i + 1
                        break

                try:
                    newly_unlocked = request.user.profile.add_win(
                        is_daily=state["is_daily"],
                        is_ranked=state["is_ranked"],
                        item_rank=item_rank,
                        game_mode="classic",
                        media_type=media_type,
                        attempts=len(guesses),
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
                    logger.warning(f"Handled error in ClassicGameGuessView: {e}")

            GameplaySession.objects.create(
                user=request.user if request.user.is_authenticated else None,
                game_mode="classic",
                media_type=media_type,
                target_item=secret_title,
                history=guesses,
                was_won=True,
            )

        # Get updated state
        revealed_hints = port.get("revealed_hints", [])
        hints = GamePresenter.format_classic_hints(
            secret_item, len(guesses), revealed_hints
        )

        return Response(
            {
                "media_type": media_type,
                "mediaType": media_type,
                "game_over": port.get("game_over", False),
                "gameOver": port.get("game_over", False),
                "guess_count": len(guesses),
                "guesses": guesses,
                "latest_guess": new_guess,
                "is_correct": is_correct,
                "hints": hints,
                "secret_title": secret_title if port.get("game_over", False) else None,
                "secret_data": secret_item if port.get("game_over", False) else None,
                "newly_unlocked_achievements": unlocked_achievements,
            }
        )


class ClassicGameRevealView(APIView):
    permission_classes = [permissions.AllowAny]

    @inject
    def post(self, request, catalog_service=Provide[Container.core.catalog_service]):
        session_service = get_session_service(request)
        port = session_service.port
        secret_title = port.get("secret_title")
        if not secret_title:
            return Response(
                {"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST
            )

        hint_type = request.data.get("hint_type")
        if not hint_type:
            return Response(
                {"error": "Hint type is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        revealed = port.get("revealed_hints", [])
        if hint_type not in revealed:
            revealed.append(hint_type)
            port.set("revealed_hints", revealed)

        # Get updated hints
        media_type = port.get("media_type", "Anime")
        data = catalog_service.get_catalog(media_type)
        secret_data = data["title_to_full_data"].get(secret_title)

        from ...presenters import GamePresenter  # noqa: E402

        guesses = port.get("guesses", [])
        hints = GamePresenter.format_classic_hints(secret_data, len(guesses), revealed)

        return Response({"revealed_hints": revealed, "hints": hints})
