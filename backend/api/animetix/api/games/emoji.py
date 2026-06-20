from animetix_project.logging_config import get_logger
from dependency_injector.wiring import Provide, inject
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from animetix.api.dependencies import get_session_service

from ...containers import Container
from ...models import GameplaySession

logger = get_logger("animetix." + __name__)

# --- EMOJI MODE ---


class EmojiGameStateView(APIView):
    permission_classes = [permissions.AllowAny]

    @inject
    def get(
        self,
        request,
        catalog_service=Provide[Container.core.catalog_service],
        emoji_service=Provide[Container.core.emoji_service],
    ):
        session_service = get_session_service(request)
        port = session_service.port
        secret = port.get("emoji_secret")
        if not secret:
            # Auto-start game
            media_type = port.get("media_type", "Anime")
            data = catalog_service.load_data(media_type)
            if not data:
                for m_type in ["Anime", "Manga", "Character"]:
                    data = catalog_service.load_data(m_type)
                    if data:
                        media_type = m_type
                        port.set("media_type", media_type)
                        break
            if data:
                secret = emoji_service.select_secret(data)
                if secret:
                    secret_data = data["title_to_full_data"].get(secret, {})
                    description = secret_data.get("description", "")
                    emoji_list = emoji_service.generate_emojis(
                        media_type, secret, description
                    )
                    port.update(
                        {
                            "emoji_secret": secret,
                            "emoji_list": emoji_list,
                            "emoji_guesses": [],
                            "emoji_game_over": False,
                            "is_daily": False,
                            "is_ranked": False,
                        }
                    )
            # Recheck secret
            secret = port.get("emoji_secret")

        if not secret:
            return Response(
                {"error": "No game in progress and auto-start failed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "media_type": port.get("media_type", "Anime"),
                "emojis": port.get("emoji_list", []),
                "guesses": port.get("emoji_guesses", []),
                "game_over": port.get("emoji_game_over", False),
                "is_daily": port.get("is_daily", False),
                "is_ranked": port.get("is_ranked", False),
                "secret_title": secret if port.get("emoji_game_over", False) else None,
            }
        )


class EmojiGameStartView(APIView):
    permission_classes = [permissions.AllowAny]

    @inject
    def post(
        self,
        request,
        catalog_service=Provide[Container.core.catalog_service],
        emoji_service=Provide[Container.core.emoji_service],
    ):
        session_service = get_session_service(request)
        port = session_service.port
        media_type = request.data.get("media_type", port.get("media_type", "Anime"))
        if media_type in ["Anime", "Manga", "Character"]:
            port.set("media_type", media_type)
        is_daily = request.data.get("is_daily", False)
        is_ranked = request.data.get("is_ranked", False)

        data = catalog_service.load_data(media_type)
        if not data:
            return Response(
                {"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if is_daily or is_ranked:
            secret = port.get("secret_title")
        else:
            secret = emoji_service.select_secret(data)

        if not secret:
            return Response(
                {"error": "Failed to select secret title"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        secret_data = data["title_to_full_data"].get(secret, {})
        description = secret_data.get("description", "")

        emoji_list = emoji_service.generate_emojis(media_type, secret, description)

        port.update(
            {
                "emoji_secret": secret,
                "emoji_list": emoji_list,
                "emoji_guesses": [],
                "emoji_game_over": False,
                "is_daily": is_daily,
                "is_ranked": is_ranked,
            }
        )

        return Response(
            {
                "status": "started",
                "media_type": media_type,
                "emojis": emoji_list,
                "guesses": [],
                "game_over": False,
                "is_daily": is_daily,
                "is_ranked": is_ranked,
            }
        )


class EmojiGameGuessView(APIView):
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
        secret = port.get("emoji_secret")
        if not secret:
            return Response(
                {"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST
            )

        if port.get("emoji_game_over", False):
            return Response(
                {"error": "Game already over"}, status=status.HTTP_400_BAD_REQUEST
            )

        guess_title = request.data.get("guess")
        if not guess_title:
            return Response(
                {"error": "Guess is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        media_type = port.get("media_type", "Anime")
        data = catalog_service.load_data(media_type)
        if not data or guess_title not in data.get("title_to_index", {}):
            return Response(
                {"error": f"Title '{guess_title}' not in catalog"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        guess_full = data["title_to_full_data"].get(guess_title)
        secret_item = data["title_to_full_data"].get(secret)

        is_correct = game_service.check_title_match(guess_title, secret_item)

        guesses = port.get("emoji_guesses", [])
        new_guess = {
            "title": guess_title,
            "title_en": guess_full.get("title_english"),
            "title_jp": guess_full.get("title_native"),
            "image": guess_full.get("image"),
            "is_correct": is_correct,
        }
        guesses.append(new_guess)
        port.set("emoji_guesses", guesses)

        unlocked_achievements = []
        if is_correct:
            port.set("emoji_game_over", True)
            if request.user.is_authenticated:
                item_rank = 100
                for i, item in enumerate(data["lookup"]):
                    if (item.get("title") or item.get("name")) == secret:
                        item_rank = i + 1
                        break
                try:
                    newly_unlocked = request.user.profile.add_win(
                        is_daily=port.get("is_daily", False),
                        is_ranked=port.get("is_ranked", False),
                        item_rank=item_rank,
                        game_mode="emoji",
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
                    logger.warning(f"Handled error in EmojiGameGuessView: {e}")

            GameplaySession.objects.create(
                user=request.user if request.user.is_authenticated else None,
                game_mode="emoji",
                media_type=media_type,
                target_item=secret,
                history=guesses,
                was_won=True,
            )

        return Response(
            {
                "media_type": media_type,
                "game_over": port.get("emoji_game_over", False),
                "guess_count": len(guesses),
                "guesses": guesses,
                "latest_guess": new_guess,
                "is_correct": is_correct,
                "secret_title": secret if port.get("emoji_game_over", False) else None,
                "newly_unlocked_achievements": unlocked_achievements,
            }
        )
