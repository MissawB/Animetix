import logging

from core.domain.services.berrix_economy import FEATURE_BX_COSTS
from core.utils.security import sanitize_html_content
from dependency_injector.wiring import Provide, inject
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from animetix.api.billing import deduct_berrix
from animetix.api.dependencies import get_session_service
from animetix.api.throttles import CpuGameThrottle

from ...containers import Container
from ...models import GameplaySession

logger = logging.getLogger("animetix.games.animinator")


class AniminatorAskView(APIView):
    # GPU-backed AI game (LLM oracle): requires login and consumes Berrix.
    permission_classes = [permissions.IsAuthenticated]

    @inject
    def post(
        self,
        request,
        animinator_service=Provide[Container.core.animinator_service],
        catalog_service=Provide[Container.core.catalog_service],
    ):
        session = get_session_service(request)
        media_type = session.get("media_type", "Anime")
        secret = session.get("animinator_secret")
        question = request.data.get("question")

        if not question:
            return Response(
                {"error": "No question provided."}, status=status.HTTP_400_BAD_REQUEST
            )

        if not secret:
            # New game: honour the universe chosen in the Akinetix lobby.
            req_media_type = request.data.get("media_type")
            if req_media_type in ("Anime", "Manga", "Character"):
                media_type = req_media_type
                session.set("media_type", media_type)
            data = catalog_service.load_data(media_type)
            if not data:
                return Response(
                    {"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND
                )
            import random  # noqa: E402

            from ...services import AKINETIX_DIFFICULTY_RANK  # noqa: E402

            # Difficulty bounds the secret (Easy = famous, Impossible = obscure).
            difficulty = request.data.get("difficulty", "Normal")
            limit = AKINETIX_DIFFICULTY_RANK.get(difficulty)
            lookup = data.get("lookup", [])
            pool = [
                (it.get("title") or it.get("name"))
                for it in (lookup[:limit] if limit else lookup)
                if (it.get("title") or it.get("name"))
                in data.get("title_to_full_data", {})
            ]
            if not pool:
                pool = list(data["title_to_full_data"].keys())
            secret = random.choice(pool)  # nosec B311
            session.set("animinator_secret", secret)
            session.set("animinator_questions_left", 20)
            session.set("animinator_chat", [])

        # Berrix deduction for the GPU oracle turn (raises 402 if balance too low).
        # Outside the try below so PaymentRequired isn't swallowed into a 500.
        deduct_berrix(
            request.user,
            FEATURE_BX_COSTS["animinator"],
            "Animinator — Oracle IA",
        )

        try:
            # On collecte le flux complet en synchrone pour renvoyer une réponse JSON (puisque le frontend l'attend ainsi)
            full_response = ""
            for token in animinator_service.ask_oracle_stream(
                media_type, secret, question
            ):
                full_response += token

            # Sécurisation de la réponse générée par l'IA
            sanitized_response = sanitize_html_content(full_response)

            chat = session.get("animinator_chat", [])
            chat.append({"q": question, "a": sanitized_response})
            session.set("animinator_chat", chat)

            q_left = session.get("animinator_questions_left", 20) - 1
            session.set("animinator_questions_left", max(0, q_left))

            if q_left <= 0:
                session.set("animinator_game_over", True)
                GameplaySession.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    game_mode="animinator",
                    media_type=media_type,
                    target_item=secret,
                    history=chat,
                    was_won=False,
                )

            return Response({"answer": sanitized_response, "questions_left": q_left})
        except Exception:
            logger.exception("Error in AniminatorAskView")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AniminatorGuessView(APIView):
    # Pure comparison (no GPU) → AllowAny; a game only exists for someone who has
    # been asking (which requires login).
    permission_classes = [permissions.AllowAny]
    throttle_classes = [
        CpuGameThrottle
    ]  # CPU game, no Bx: minute-cap only, never the day cap

    @inject
    def post(
        self,
        request,
        animinator_service=Provide[Container.core.animinator_service],
    ):
        session = get_session_service(request)
        secret = session.get("animinator_secret")
        if not secret:
            return Response(
                {"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST
            )

        guess = request.data.get("guess", "")
        if not guess:
            return Response(
                {"error": "guess is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        correct = animinator_service.check_guess(guess, secret)
        if correct:
            session.set("animinator_game_over", True)
            # Clear the secret so the next question starts a fresh game (replay).
            session.set("animinator_secret", "")
            media_type = session.get("media_type", "Anime")
            chat = session.get("animinator_chat", [])
            if request.user.is_authenticated:
                try:
                    request.user.profile.add_win(
                        game_mode="animinator",
                        media_type=media_type,
                        attempts=len(chat),
                    )
                except Exception as e:
                    logger.warning(f"Handled error in AniminatorGuessView: {e}")
            GameplaySession.objects.create(
                user=request.user if request.user.is_authenticated else None,
                game_mode="animinator",
                media_type=media_type,
                target_item=secret,
                history=chat,
                was_won=True,
            )

        return Response(
            {
                "correct": correct,
                "game_over": correct,
                "secret": secret if correct else None,
            }
        )
