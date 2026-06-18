from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from dependency_injector.wiring import inject, Provide
from ...containers import Container
from animetix.api.dependencies import get_session_service
from ...models import GameplaySession

from core.utils.security import sanitize_html_content


class AniminatorAskView(APIView):
    permission_classes = [permissions.AllowAny]

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
            data = catalog_service.load_data(media_type)
            if not data:
                return Response(
                    {"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND
                )
            import random  # noqa: E402

            secret = random.choice(list(data["title_to_full_data"].keys()))
            session.set("animinator_secret", secret)
            session.set("animinator_questions_left", 20)
            session.set("animinator_chat", [])

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
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
