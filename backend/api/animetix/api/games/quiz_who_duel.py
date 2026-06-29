"""2-player 'Qui est-ce ?' (turn-based versus).

Each player is assigned a secret character on a shared board. Players alternate
turns: on your turn you ask one attribute question about the OPPONENT's secret,
eliminate the non-matching portraits on your side, and may guess. First to guess
the opponent's secret wins. Room-based (code), REST + client polling. CPU
(attribute matching, reuses the Akinetix engine) — no Berrix.
"""

import random
import string

from animetix_project.logging_config import get_logger
from dependency_injector.wiring import Provide, inject
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ...containers import Container
from ...models import GameplaySession, QuizWhoRoom

logger = get_logger("animetix." + __name__)

BOARD_SIZE = 16
MAX_QUESTIONS_OFFERED = 24


def _code():
    return "".join(
        random.choices(string.ascii_uppercase + string.digits, k=5)
    )  # nosec B311


def _title(item):
    return item.get("title") or item.get("name") or "?"


def _build_board(catalog, engine, fine, limit):
    pool = [
        it
        for it in catalog["db"][:limit]
        if it.get("image") and (it.get("title") or it.get("name"))
    ]
    if len(pool) < 4:
        return [], []
    board_items = random.sample(pool, min(BOARD_SIZE, len(pool)))  # nosec B311
    n = len(board_items)
    attr_count = {}
    for it in board_items:
        for at in engine._item_attribute_set(it, fine):
            attr_count[at] = attr_count.get(at, 0) + 1
    discriminating = [at for at, c in attr_count.items() if 0 < c < n]
    discriminating.sort(key=lambda at: abs(attr_count[at] - n / 2))
    questions, seen = [], set()
    for at in discriminating:
        label = engine.formatter.format(at)
        if label in seen:
            continue
        seen.add(label)
        questions.append({"attr": at, "label": label})
        if len(questions) >= MAX_QUESTIONS_OFFERED:
            break
    board = [
        {"id": str(it.get("id")), "title": _title(it), "image": it.get("image")}
        for it in board_items
    ]
    return board, questions


def _player_num(room, user):
    if room.player1_id == user.id:
        return 1
    if room.player2_id == user.id:
        return 2
    return 0


def _state(room, num):
    by_id = {b["id"]: b for b in room.board}
    my_secret = room.secret1 if num == 1 else room.secret2
    my_elim = room.eliminated1 if num == 1 else room.eliminated2
    return {
        "room_code": room.room_code,
        "media_type": room.media_type,
        "difficulty": room.difficulty,
        "board": room.board,
        "questions": room.questions,
        "your_player": num,
        "your_secret_id": my_secret,
        "your_secret_title": (by_id.get(my_secret) or {}).get("title"),
        "your_eliminated": my_elim,
        "opponent_joined": room.player2_id is not None,
        "your_turn": (
            not room.is_finished and room.player2_id is not None and room.turn == num
        ),
        "last_answer": room.last_answer or None,
        "finished": room.is_finished,
        "winner": room.winner,
        "you_won": room.is_finished and room.winner == num,
        "player1": room.player1.username,
        "player2": room.player2.username if room.player2_id else None,
    }


class QuizWhoDuelCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @inject
    def post(
        self,
        request,
        catalog_service=Provide[Container.core.catalog_service],
        akinetix_service=Provide[Container.core.akinetix_service],
    ):
        media_type = request.data.get("media_type", "Anime")
        difficulty = request.data.get("difficulty", "Normal")
        catalog = catalog_service.load_data(media_type)
        if not catalog or not catalog.get("db"):
            return Response(
                {"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND
            )
        from ...services import AKINETIX_DIFFICULTY_RANK  # noqa: E402

        limit = AKINETIX_DIFFICULTY_RANK.get(difficulty) or 500
        fine = catalog_service.get_akinetix_attributes()
        board, questions = _build_board(catalog, akinetix_service.engine, fine, limit)
        if not board:
            return Response(
                {"error": "Not enough candidates for this universe."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        code = _code()
        while QuizWhoRoom.objects.filter(room_code=code).exists():
            code = _code()
        room = QuizWhoRoom.objects.create(
            room_code=code,
            player1=request.user,
            media_type=media_type,
            difficulty=difficulty,
            board=board,
            questions=questions,
            secret1=random.choice(board)["id"],  # nosec B311
            turn=1,
        )
        return Response(_state(room, 1), status=status.HTTP_201_CREATED)


class QuizWhoDuelJoinView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        code = request.data.get("room_code", "").upper()
        try:
            room = QuizWhoRoom.objects.get(room_code=code, is_finished=False)
        except QuizWhoRoom.DoesNotExist:
            return Response(
                {"error": "Salle introuvable."}, status=status.HTTP_404_NOT_FOUND
            )

        num = _player_num(room, request.user)
        if num:  # already in the room
            return Response(_state(room, num))
        if room.player2_id is not None:
            return Response(
                {"error": "Salle complète."}, status=status.HTTP_400_BAD_REQUEST
            )

        room.player2 = request.user
        ids = [b["id"] for b in room.board if b["id"] != room.secret1]
        room.secret2 = random.choice(ids) if ids else room.secret1  # nosec B311
        room.save(update_fields=["player2", "secret2"])
        return Response(_state(room, 2))


class QuizWhoDuelStateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, room_code):
        try:
            room = QuizWhoRoom.objects.get(room_code=room_code.upper())
        except QuizWhoRoom.DoesNotExist:
            return Response(
                {"error": "Salle introuvable."}, status=status.HTTP_404_NOT_FOUND
            )
        num = _player_num(room, request.user)
        if not num:
            return Response(
                {"error": "Tu n'es pas dans cette salle."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(_state(room, num))


def _opponent_secret(room, num):
    return room.secret2 if num == 1 else room.secret1


class QuizWhoDuelAskView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @inject
    def post(
        self,
        request,
        catalog_service=Provide[Container.core.catalog_service],
        akinetix_service=Provide[Container.core.akinetix_service],
    ):
        code = request.data.get("room_code", "").upper()
        attribute = request.data.get("attribute")
        try:
            room = QuizWhoRoom.objects.get(room_code=code)
        except QuizWhoRoom.DoesNotExist:
            return Response(
                {"error": "Salle introuvable."}, status=status.HTTP_404_NOT_FOUND
            )
        num = _player_num(room, request.user)
        if not num:
            return Response({"error": "Interdit."}, status=status.HTTP_403_FORBIDDEN)
        if room.is_finished or room.player2_id is None:
            return Response(
                {"error": "Partie non active."}, status=status.HTTP_400_BAD_REQUEST
            )
        if room.turn != num:
            return Response(
                {"error": "Ce n'est pas ton tour."}, status=status.HTTP_400_BAD_REQUEST
            )
        if not attribute:
            return Response(
                {"error": "attribute requis."}, status=status.HTTP_400_BAD_REQUEST
            )

        catalog = catalog_service.load_data(room.media_type)
        by_id = (catalog or {}).get("id_to_full_data", {})
        fine = catalog_service.get_akinetix_attributes()
        engine = akinetix_service.engine

        target = _opponent_secret(room, num)
        target_item = by_id.get(str(target))
        if not target_item:
            return Response(
                {"error": "Secret indisponible."}, status=status.HTTP_400_BAD_REQUEST
            )
        secret_has = bool(
            engine._check_attribute_instance(target_item, attribute, fine)
        )

        elim = set(room.eliminated1 if num == 1 else room.eliminated2)
        newly = []
        for b in room.board:
            cid = b["id"]
            if cid in elim or cid == str(target):
                continue
            it = by_id.get(cid)
            if it is None:
                continue
            if (
                bool(engine._check_attribute_instance(it, attribute, fine))
                != secret_has
            ):
                elim.add(cid)
                newly.append(cid)

        if num == 1:
            room.eliminated1 = list(elim)
        else:
            room.eliminated2 = list(elim)
        label = next(
            (q["label"] for q in room.questions if q["attr"] == attribute), attribute
        )
        room.last_answer = {
            "by": num,
            "label": label,
            "answer": "OUI" if secret_has else "NON",
        }
        room.turn = 2 if num == 1 else 1
        room.save()
        return Response({"answer": "OUI" if secret_has else "NON", "eliminated": newly})


class QuizWhoDuelGuessView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        code = request.data.get("room_code", "").upper()
        guess_id = str(request.data.get("guess_id", ""))
        try:
            room = QuizWhoRoom.objects.get(room_code=code)
        except QuizWhoRoom.DoesNotExist:
            return Response(
                {"error": "Salle introuvable."}, status=status.HTTP_404_NOT_FOUND
            )
        num = _player_num(room, request.user)
        if not num:
            return Response({"error": "Interdit."}, status=status.HTTP_403_FORBIDDEN)
        if room.is_finished or room.player2_id is None:
            return Response(
                {"error": "Partie non active."}, status=status.HTTP_400_BAD_REQUEST
            )
        if room.turn != num:
            return Response(
                {"error": "Ce n'est pas ton tour."}, status=status.HTTP_400_BAD_REQUEST
            )

        target = _opponent_secret(room, num)
        correct = guess_id == str(target)
        by_id = {b["id"]: b for b in room.board}
        secret_title = (by_id.get(str(target)) or {}).get("title")

        if correct:
            room.winner = num
            room.is_finished = True
            room.save(update_fields=["winner", "is_finished"])
            try:
                request.user.profile.add_win(
                    game_mode="quiz_who_duel", media_type=room.media_type
                )
            except Exception as e:
                logger.warning(f"Handled error in QuizWhoDuelGuessView: {e}")
            GameplaySession.objects.create(
                user=request.user,
                game_mode="quiz_who_duel",
                media_type=room.media_type,
                target_item=secret_title or "",
                history=[],
                was_won=True,
            )
            return Response(
                {
                    "correct": True,
                    "finished": True,
                    "winner": num,
                    "secret_title": secret_title,
                }
            )

        # Wrong guess: flip that tile off on your side and pass the turn.
        elim = set(room.eliminated1 if num == 1 else room.eliminated2)
        elim.add(guess_id)
        if num == 1:
            room.eliminated1 = list(elim)
        else:
            room.eliminated2 = list(elim)
        room.last_answer = {"by": num, "label": "Tentative", "answer": "RATÉ"}
        room.turn = 2 if num == 1 else 1
        room.save()
        return Response({"correct": False, "finished": False})
