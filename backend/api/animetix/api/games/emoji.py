import unicodedata

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


def _norm(s):
    """Casefold + strip accents so 'Démon' matches 'demon' and 'DEMON'."""
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    return s.casefold().strip()


# --- EMOJI MODE (CPU only) ---
# Emojis are derived offline from each title's important words via semantic
# embeddings (pipeline/games/build_emoji_sequences.py) and revealed one at a time,
# vaguest first. No LLM, no GPU, no Berrix → AllowAny + throttle-exempt.


def _revealed(port):
    """Emojis shown so far: 1 at the start, +1 per wrong guess, all when won."""
    full = port.get("emoji_list") or []
    if not isinstance(full, list):  # legacy sessions stored a raw emoji string
        full = []
    if port.get("emoji_game_over", False):
        return full
    wrong = sum(1 for g in port.get("emoji_guesses", []) if not g.get("is_correct"))
    return full[: min(len(full), 1 + wrong)]


EMOJI_MEDIA_TYPES = ["Anime", "Manga", "Character"]
EMOJI_DIFFICULTIES = ["Easy", "Normal", "Hard", "Impossible"]


def _difficulty_limit(difficulty):
    """Popularity ceiling for the secret pool. Easy = only the most famous
    works, Impossible = the whole catalogue (deep cuts)."""
    from ...services import AKINETIX_DIFFICULTY_RANK

    return AKINETIX_DIFFICULTY_RANK.get(difficulty, AKINETIX_DIFFICULTY_RANK["Normal"])


def _start_game(port, catalog_service, emoji_service, media_type, difficulty="Normal"):
    """Pick a secret + build its precomputed emoji sequence (no LLM)."""
    data = catalog_service.load_data(media_type)
    if not data or not data.get("db"):
        for m_type in EMOJI_MEDIA_TYPES:
            data = catalog_service.load_data(m_type)
            if data and data.get("db"):
                media_type = m_type
                break
    if not data or not data.get("db"):
        return None, media_type
    secret = emoji_service.select_secret(data, limit=_difficulty_limit(difficulty))
    if not secret:
        return None, media_type
    item = data["title_to_full_data"].get(secret, {})
    sequences = catalog_service.get_emoji_sequences()
    emoji_list = emoji_service.build_sequence(sequences, media_type, item)
    port.update(
        {
            "media_type": media_type,
            "difficulty": difficulty,
            "emoji_secret": secret,
            "emoji_list": emoji_list,
            "emoji_guesses": [],
            "emoji_game_over": False,
            "is_daily": False,
            "is_ranked": False,
        }
    )
    return secret, media_type


class EmojiGameStateView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [
        CpuGameThrottle
    ]  # CPU game, no Bx: minute-cap only, never the day cap

    @inject
    def get(
        self,
        request,
        catalog_service=Provide[Container.core.catalog_service],
        emoji_service=Provide[Container.core.emoji_service],
    ):
        port = get_session_service(request).port
        secret = port.get("emoji_secret")
        # Rebuild if there is no game OR the stored sequence is legacy/corrupt
        # (old sessions kept emoji_list as a raw string, which the SPA can't map).
        if not secret or not isinstance(port.get("emoji_list"), list):
            media_type = port.get("media_type", "Anime")
            secret, media_type = _start_game(
                port,
                catalog_service,
                emoji_service,
                media_type,
                port.get("difficulty", "Normal"),
            )
        if not secret:
            return Response(
                {"error": "No game in progress and auto-start failed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "media_type": port.get("media_type", "Anime"),
                "difficulty": port.get("difficulty", "Normal"),
                "emojis": _revealed(port),
                "total_emojis": len(port.get("emoji_list", []) or []),
                "guesses": port.get("emoji_guesses", []),
                "game_over": port.get("emoji_game_over", False),
                "is_daily": port.get("is_daily", False),
                "is_ranked": port.get("is_ranked", False),
                "secret_title": secret if port.get("emoji_game_over", False) else None,
            }
        )


class EmojiGameStartView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [
        CpuGameThrottle
    ]  # CPU game, no Bx: minute-cap only, never the day cap

    @inject
    def post(
        self,
        request,
        catalog_service=Provide[Container.core.catalog_service],
        emoji_service=Provide[Container.core.emoji_service],
    ):
        port = get_session_service(request).port
        media_type = request.data.get("media_type", port.get("media_type", "Anime"))
        if media_type not in EMOJI_MEDIA_TYPES:
            media_type = "Anime"
        difficulty = request.data.get("difficulty", port.get("difficulty", "Normal"))
        if difficulty not in EMOJI_DIFFICULTIES:
            difficulty = "Normal"
        secret, media_type = _start_game(
            port, catalog_service, emoji_service, media_type, difficulty
        )
        if not secret:
            return Response(
                {"error": "Failed to start the game"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(
            {
                "status": "started",
                "media_type": media_type,
                "difficulty": difficulty,
                "emojis": _revealed(port),
                "total_emojis": len(port.get("emoji_list", []) or []),
                "guesses": [],
                "game_over": False,
                "is_daily": False,
                "is_ranked": False,
            }
        )


class EmojiGameGuessView(APIView):
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
        port = get_session_service(request).port
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
                "difficulty": port.get("difficulty", "Normal"),
                "emojis": _revealed(port),
                "total_emojis": len(port.get("emoji_list", []) or []),
                "game_over": port.get("emoji_game_over", False),
                "guess_count": len(guesses),
                "guesses": guesses,
                "latest_guess": new_guess,
                "is_correct": is_correct,
                "secret_title": secret if port.get("emoji_game_over", False) else None,
                "newly_unlocked_achievements": unlocked_achievements,
            }
        )


class EmojiGameGiveUpView(APIView):
    """Abandon the current game: reveal the answer and record a loss.

    CPU game → AllowAny + throttle-exempt. No win credited.
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = [
        CpuGameThrottle
    ]  # CPU game, no Bx: minute-cap only, never the day cap

    def post(self, request):
        port = get_session_service(request).port
        secret = port.get("emoji_secret")
        if not secret:
            return Response(
                {"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST
            )

        already_over = port.get("emoji_game_over", False)
        if not already_over:
            port.set("emoji_game_over", True)
            GameplaySession.objects.create(
                user=request.user if request.user.is_authenticated else None,
                game_mode="emoji",
                media_type=port.get("media_type", "Anime"),
                target_item=secret,
                history=port.get("emoji_guesses", []),
                was_won=False,
            )

        return Response(
            {
                "media_type": port.get("media_type", "Anime"),
                "difficulty": port.get("difficulty", "Normal"),
                "emojis": _revealed(port),  # game over → full sequence revealed
                "total_emojis": len(port.get("emoji_list", []) or []),
                "guesses": port.get("emoji_guesses", []),
                "game_over": True,
                "won": False,
                "secret_title": secret,
            }
        )


class EmojiGameSuggestView(APIView):
    """Rich autocomplete for the guess box.

    Suggestions are drawn from the SAME catalog the game validates against, so
    every suggestion is guessable. Each entry carries the native + English title
    and the cover image. CPU only → AllowAny + throttle-exempt.
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = [
        CpuGameThrottle
    ]  # CPU game, no Bx: minute-cap only, never the day cap
    MAX_SUGGESTIONS = 8

    @inject
    def get(self, request, catalog_service=Provide[Container.core.catalog_service]):
        q = _norm(request.query_params.get("q", ""))
        if len(q) < 2:
            return Response({"suggestions": []})

        port = get_session_service(request).port
        media_type = port.get("media_type", "Anime")
        data = catalog_service.load_data(media_type)
        if not data or not data.get("db"):
            return Response({"suggestions": []})

        starts, contains = [], []
        for item in data["db"]:
            title = item.get("title") or item.get("name") or ""
            entry = {
                "title": title,
                "title_english": item.get("title_english"),
                "title_native": item.get("title_native"),
                "image": item.get("image"),
            }
            fields = [
                _norm(title),
                _norm(item.get("title_english")),
                _norm(item.get("title_native")),
            ]
            fields = [f for f in fields if f]
            if any(f.startswith(q) for f in fields):
                starts.append(entry)
            elif any(q in f for f in fields):
                contains.append(entry)
            if len(starts) >= self.MAX_SUGGESTIONS:
                break

        return Response({"suggestions": (starts + contains)[: self.MAX_SUGGESTIONS]})
