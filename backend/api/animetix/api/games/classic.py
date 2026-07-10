from animetix_project.logging_config import get_logger
from dependency_injector.wiring import Provide, inject
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from animetix.api.dependencies import get_session_service
from animetix.api.throttles import CpuGameThrottle

from ...containers import Container
from ...models import GameplaySession

logger = get_logger("animetix." + __name__)

# Hint keys the player may pick/order in the lobby.
# Keep in sync with CLASSIC_HINT_ORDER in animetix/presenters.py.
HINT_TYPES = ("year", "origin", "tags", "genres", "studio", "letter", "words", "desc")


def _sanitize_hint_config(raw):
    """Keep only valid hint keys, preserve order, drop duplicates.

    A list is honoured as-is — including an empty list, which means "no hints"
    (the Tryhard mode). Only ``None``/invalid input falls back to the full
    default selection (e.g. legacy sessions or API calls without a config).
    """
    if isinstance(raw, list):
        return list(dict.fromkeys(h for h in raw if h in HINT_TYPES))
    return list(HINT_TYPES)


def _daily_score(attempts, hints_revealed):
    """Daily score: 100 at best, minus penalties for extra guesses / revealed hints."""
    return max(10, 100 - (attempts - 1) * 10 - hints_revealed * 5)


# --- CLASSIC MODE ---


class ClassicGameStateView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [
        CpuGameThrottle
    ]  # CPU game, no Bx: minute-cap only, never the day cap

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

        hint_config = _sanitize_hint_config(state.get("hint_config"))
        hints = GamePresenter.format_classic_hints(
            secret_data,
            len(state["guesses"]),
            state["revealed_hints"],
            hint_config=hint_config,
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


class ClassicGameTitlesView(APIView):
    """Catalog titles for the guess autocomplete (same catalog used to validate)."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [
        CpuGameThrottle
    ]  # CPU game, no Bx: minute-cap only, never the day cap

    @inject
    def get(self, request, catalog_service=Provide[Container.core.catalog_service]):
        session_service = get_session_service(request)
        media_type = session_service.get_classic_state().get("media_type") or "Anime"
        data = catalog_service.get_catalog(media_type)
        titles = sorted((data or {}).get("title_to_full_data", {}).keys())
        return Response({"titles": titles})


class ClassicGameStartView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [
        CpuGameThrottle
    ]  # CPU game, no Bx: minute-cap only, never the day cap

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
        daily = bool(request.data.get("daily", False))
        hint_config = _sanitize_hint_config(request.data.get("hint_config"))

        port.update({"media_type": media_type, "difficulty": difficulty})

        data = catalog_service.get_catalog(media_type)
        if not data:
            return Response(
                {"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if override_secret and getattr(request.user, "is_staff", False):
            secret_title = override_secret
            port.update({"is_daily": False, "is_ranked": False, "daily_date": None})
        elif daily:
            # Deterministic target of the day for this media type (same for all).
            # An optional daily_date lets players replay a past day (capped: today
            # and at most 30 days back).
            import datetime as _dt  # noqa: E402

            today = _dt.date.today()
            day = today
            raw_date = request.data.get("daily_date")
            if raw_date:
                try:
                    parsed = _dt.date.fromisoformat(str(raw_date))
                    if parsed <= today and (today - parsed).days <= 30:
                        day = parsed
                except ValueError:
                    logger.debug("Ignoring invalid daily date param: %r", raw_date)
            port.update(
                {"is_daily": True, "is_ranked": False, "daily_date": day.isoformat()}
            )
            secret_title = game_service.select_daily_secret(media_type, day)
        else:
            if override_secret:
                logger.warning(
                    f"User {request.user} tried to override secret without staff permissions."
                )
            port.update({"is_daily": False, "is_ranked": False, "daily_date": None})
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
                "hint_config": hint_config,
            }
        )

        from ...presenters import GamePresenter  # noqa: E402

        secret_data = data["title_to_full_data"].get(secret_title)
        hints = GamePresenter.format_classic_hints(
            secret_data, 0, [], hint_config=hint_config
        )

        return Response(
            {
                "status": "started",
                "media_type": media_type,
                "mediaType": media_type,
                "difficulty": difficulty,
                "is_daily": daily,
                "isDaily": daily,
                "is_ranked": False,
                "game_over": False,
                "gameOver": False,
                "guess_count": 0,
                "guesses": [],
                "hints": hints,
            }
        )


class ClassicGameGuessView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [
        CpuGameThrottle
    ]  # CPU game, no Bx: minute-cap only, never the day cap

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
            "hint_config": _sanitize_hint_config(port.get("hint_config")),
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
        daily_score = None
        if is_correct:
            port.set("game_over", True)
            if state["is_daily"]:
                daily_score = _daily_score(
                    len(guesses), len(port.get("revealed_hints", []))
                )
                if request.user.is_authenticated:
                    import datetime as _dt  # noqa: E402

                    from ...models import DailyResult  # noqa: E402

                    raw_day = port.get("daily_date") or _dt.date.today().isoformat()
                    try:
                        day = _dt.date.fromisoformat(str(raw_day))
                    except ValueError:
                        day = _dt.date.today()
                    try:
                        obj, created = DailyResult.objects.get_or_create(
                            user=request.user,
                            date=day,
                            media_type=media_type,
                            defaults={"score": daily_score, "attempts": len(guesses)},
                        )
                        # Keep the best score on replay.
                        if not created and daily_score > obj.score:
                            obj.score = daily_score
                            obj.attempts = len(guesses)
                            obj.save(update_fields=["score", "attempts"])
                    except Exception as e:
                        logger.warning(f"Daily result save failed: {e}")
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
            secret_item, len(guesses), revealed_hints, hint_config=state["hint_config"]
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
                "daily_score": daily_score,
            }
        )


class ClassicGameRevealView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [
        CpuGameThrottle
    ]  # CPU game, no Bx: minute-cap only, never the day cap

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
        hint_config = _sanitize_hint_config(port.get("hint_config"))
        if not hint_type or hint_type not in hint_config:
            return Response(
                {"error": "Invalid hint type"}, status=status.HTTP_400_BAD_REQUEST
            )

        from ...presenters import GamePresenter  # noqa: E402

        media_type = port.get("media_type", "Anime")
        data = catalog_service.get_catalog(media_type)
        secret_data = data["title_to_full_data"].get(secret_title)
        guesses = port.get("guesses", [])
        revealed = port.get("revealed_hints", [])

        # The hint must have unlocked (enough guesses) before it can be revealed.
        current = GamePresenter.format_classic_hints(
            secret_data, len(guesses), revealed, hint_config=hint_config
        )
        if not current.get(hint_type, {}).get("can_reveal"):
            return Response(
                {"error": "Hint not yet unlocked"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if hint_type not in revealed:
            revealed.append(hint_type)
            port.set("revealed_hints", revealed)

        hints = GamePresenter.format_classic_hints(
            secret_data, len(guesses), revealed, hint_config=hint_config
        )
        return Response({"revealed_hints": revealed, "hints": hints})
