"""'Qui est-ce ?' (Guess Who) — attribute-board deduction.

A board of candidate works/characters is shown; the engine holds a secret among
them. The player asks attribute questions (genre, era, tags, studio, character
traits — the same attributes Akinetix uses); the secret's answer eliminates the
board candidates that don't match, until the player clicks one to guess.

Pure CPU (attribute matching, no LLM) → AllowAny, no Berrix, like Akinetix
classic. Reuses the Akinetix engine's attribute helpers for consistency.
"""

import random

from animetix_project.logging_config import get_logger
from dependency_injector.wiring import Provide, inject
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from animetix.api.dependencies import get_session_service

from ...containers import Container
from ...models import GameplaySession

logger = get_logger("animetix." + __name__)

BOARD_SIZE = 16
# Sample the board from the most popular items so portraits are recognisable.
POPULAR_POOL = 400
MAX_QUESTIONS_OFFERED = 24
SK = "quizwho_"  # session-key prefix


def _title(item):
    return item.get("title") or item.get("name") or "?"


class QuiEstCeStartView(APIView):
    permission_classes = [permissions.AllowAny]

    @inject
    def post(
        self,
        request,
        catalog_service=Provide[Container.core.catalog_service],
        akinetix_service=Provide[Container.core.akinetix_service],
    ):
        session = get_session_service(request)
        port = session.port
        media_type = request.data.get("media_type", port.get("media_type", "Anime"))
        if media_type in ("Anime", "Manga", "Character"):
            port.set("media_type", media_type)

        catalog = catalog_service.load_data(media_type)
        if not catalog or not catalog.get("db"):
            return Response(
                {"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND
            )

        fine = catalog_service.get_akinetix_attributes()
        engine = akinetix_service.engine

        # Difficulty bounds the board pool (Easy = famous, Impossible = obscure).
        from ...services import AKINETIX_DIFFICULTY_RANK  # noqa: E402

        difficulty = request.data.get("difficulty", "Normal")
        limit = AKINETIX_DIFFICULTY_RANK.get(difficulty) or POPULAR_POOL
        pool = [
            it
            for it in catalog["db"][:limit]
            if it.get("image") and (it.get("title") or it.get("name"))
        ]
        if len(pool) < 4:
            return Response(
                {"error": "Not enough candidates with images for this universe."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        board_items = random.sample(pool, min(BOARD_SIZE, len(pool)))  # nosec B311
        secret = random.choice(board_items)  # nosec B311
        n = len(board_items)

        # Discriminating attributes: present in some-but-not-all board items.
        attr_count: dict[str, int] = {}
        for it in board_items:
            for at in engine._item_attribute_set(it, fine):
                attr_count[at] = attr_count.get(at, 0) + 1
        discriminating = [at for at, c in attr_count.items() if 0 < c < n]
        # Best splitters first (closest to halving the board).
        discriminating.sort(key=lambda at: abs(attr_count[at] - n / 2))

        questions = []
        seen_labels = set()
        for at in discriminating:
            label = engine.formatter.format(at)
            if label in seen_labels:
                continue
            seen_labels.add(label)
            questions.append({"attr": at, "label": label})
            if len(questions) >= MAX_QUESTIONS_OFFERED:
                break

        board_ids = [str(it.get("id")) for it in board_items]
        port.set(SK + "secret", str(secret.get("id")))
        port.set(SK + "board", board_ids)
        port.set(SK + "eliminated", [])
        port.set(SK + "asked", [])
        port.set(SK + "over", False)
        port.set(SK + "media_type", media_type)

        return Response(
            {
                "media_type": media_type,
                "board": [
                    {
                        "id": str(it.get("id")),
                        "title": _title(it),
                        "image": it.get("image"),
                    }
                    for it in board_items
                ],
                "questions": questions,
                "asked_count": 0,
                "game_over": False,
            }
        )


class QuiEstCeAskView(APIView):
    permission_classes = [permissions.AllowAny]

    @inject
    def post(
        self,
        request,
        catalog_service=Provide[Container.core.catalog_service],
        akinetix_service=Provide[Container.core.akinetix_service],
    ):
        session = get_session_service(request)
        port = session.port
        secret_id = port.get(SK + "secret")
        if not secret_id or port.get(SK + "over"):
            return Response(
                {"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST
            )

        attribute = request.data.get("attribute")
        if not attribute:
            return Response(
                {"error": "attribute is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        media_type = port.get(SK + "media_type", "Anime")
        catalog = catalog_service.load_data(media_type)
        if not catalog:
            return Response(
                {"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND
            )
        by_id = catalog.get("id_to_full_data", {})
        fine = catalog_service.get_akinetix_attributes()
        engine = akinetix_service.engine

        secret_item = by_id.get(str(secret_id))
        if not secret_item:
            return Response(
                {"error": "Secret unavailable"}, status=status.HTTP_400_BAD_REQUEST
            )
        secret_has = bool(
            engine._check_attribute_instance(secret_item, attribute, fine)
        )

        board = port.get(SK + "board", [])
        eliminated = set(port.get(SK + "eliminated", []))
        newly = []
        for cid in board:
            if cid in eliminated or cid == str(secret_id):
                continue
            it = by_id.get(cid)
            if it is None:
                continue
            if (
                bool(engine._check_attribute_instance(it, attribute, fine))
                != secret_has
            ):
                eliminated.add(cid)
                newly.append(cid)

        asked = port.get(SK + "asked", [])
        asked.append(attribute)
        port.set(SK + "asked", asked)
        port.set(SK + "eliminated", list(eliminated))

        remaining = [c for c in board if c not in eliminated]
        return Response(
            {
                "answer": "OUI" if secret_has else "NON",
                "eliminated": newly,
                "remaining_count": len(remaining),
                "asked_count": len(asked),
            }
        )


class QuiEstCeGuessView(APIView):
    permission_classes = [permissions.AllowAny]

    @inject
    def post(
        self,
        request,
        catalog_service=Provide[Container.core.catalog_service],
    ):
        session = get_session_service(request)
        port = session.port
        secret_id = port.get(SK + "secret")
        if not secret_id or port.get(SK + "over"):
            return Response(
                {"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST
            )

        guess_id = str(request.data.get("guess_id", ""))
        correct = guess_id == str(secret_id)

        media_type = port.get(SK + "media_type", "Anime")
        catalog = catalog_service.load_data(media_type)
        by_id = (catalog or {}).get("id_to_full_data", {})
        secret_title = _title(by_id.get(str(secret_id), {}))

        if correct:
            port.set(SK + "over", True)
            if request.user.is_authenticated:
                try:
                    request.user.profile.add_win(
                        game_mode="quiz_who",
                        media_type=media_type,
                        attempts=len(port.get(SK + "asked", [])),
                    )
                except Exception as e:
                    logger.warning(f"Handled error in QuiEstCeGuessView: {e}")
            GameplaySession.objects.create(
                user=request.user if request.user.is_authenticated else None,
                game_mode="quiz_who",
                media_type=media_type,
                target_item=secret_title,
                history=[{"asked": port.get(SK + "asked", [])}],
                was_won=True,
            )
            return Response(
                {"correct": True, "game_over": True, "secret_title": secret_title}
            )

        # Wrong guess: flip that tile off and keep playing.
        eliminated = set(port.get(SK + "eliminated", []))
        eliminated.add(guess_id)
        port.set(SK + "eliminated", list(eliminated))
        return Response(
            {"correct": False, "game_over": False, "eliminated": [guess_id]}
        )
