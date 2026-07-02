"""Real-time 2-player "Qui est-ce ?" (Guess Who) duel over WebSocket.

Each player gets a secret character from a shared 16-portrait board; on your turn
you ask one yes/no attribute question about the OPPONENT's secret, cross off the
non-matching portraits on your side, and may guess. First to guess the opponent's
secret wins. Players are keyed by a stable client id (cid) — no login, join by
code (consistent with Undercover / Code Manga). CPU only (Akinetix attribute
engine), no Berrix.
"""

import json
import random
from urllib.parse import parse_qs

from asgiref.sync import sync_to_async

from ..containers import get_container
from .base import BaseConsumer, state_adapter

BOARD_SIZE = 16
MAX_QUESTIONS = 24
UNIVERSES = {"Anime", "Manga", "Character"}
DIFFICULTIES = {"Easy", "Normal", "Hard", "Impossible"}


def _title(item):
    return item.get("title") or item.get("name") or "?"


def _build_board(media_type, difficulty):
    """Sync: sample a board + discriminating attribute questions. Runs in a
    thread via sync_to_async. Returns (board, questions)."""
    from ..services import AKINETIX_DIFFICULTY_RANK

    container = get_container()
    catalog = container.core.catalog_service().load_data(media_type)
    if not catalog or not catalog.get("db"):
        return [], []
    limit = AKINETIX_DIFFICULTY_RANK.get(difficulty) or 500
    fine = container.core.catalog_service().get_akinetix_attributes()
    engine = container.core.akinetix_service().engine

    pool = [
        it
        for it in catalog["db"][:limit]
        if it.get("image") and (it.get("title") or it.get("name"))
    ]
    if len(pool) < 8:
        return [], []
    board_items = random.sample(pool, min(BOARD_SIZE, len(pool)))
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
        if len(questions) >= MAX_QUESTIONS:
            break
    board = [
        {"id": str(it.get("id")), "title": _title(it), "image": it.get("image")}
        for it in board_items
    ]
    return board, questions


def _resolve_ask(media_type, attribute, target_id, board, eliminated):
    """Sync: compute the yes/no answer for the opponent's secret and the newly
    eliminated (non-matching) portraits. Returns (secret_has, new_eliminated)."""
    container = get_container()
    cs = container.core.catalog_service()
    catalog = cs.load_data(media_type)
    by_id = (catalog or {}).get("id_to_full_data", {})
    fine = cs.get_akinetix_attributes()
    engine = container.core.akinetix_service().engine

    target_item = by_id.get(str(target_id))
    if not target_item:
        return None, list(eliminated)
    secret_has = bool(engine._check_attribute_instance(target_item, attribute, fine))
    elim = set(eliminated)
    for b in board:
        cid = b["id"]
        if cid in elim or cid == str(target_id):
            continue
        it = by_id.get(cid)
        if it is None:
            continue
        if bool(engine._check_attribute_instance(it, attribute, fine)) != secret_has:
            elim.add(cid)
    return secret_has, list(elim)


class QuizWhoConsumer(BaseConsumer):
    async def get_room(self):
        return await state_adapter.get_state(f"quizwho_room_{self.room_code}")

    async def save_room(self, room):
        await state_adapter.set_state(
            f"quizwho_room_{self.room_code}", room, timeout=3600
        )

    def _fresh_room(self):
        return {
            "host": None,
            "players": {},  # cid -> {name, num, channel}
            "state": "lobby",  # lobby | playing | ended
            "media_type": "Character",
            "difficulty": "Normal",
            "board": [],
            "questions": [],
            "secrets": {},  # "1"/"2" -> board id
            "eliminated": {"1": [], "2": []},
            "turn": 1,
            "last_answer": None,
            "winner": None,
            "messages": [],
        }

    # ── Connection ──────────────────────────────────────────────────────────
    async def connect(self):
        self.room_code = self.scope["url_route"]["kwargs"]["room_code"].upper()
        self.room_group_name = f"quizwho_{self.room_code}"
        qs = parse_qs(self.scope.get("query_string", b"").decode())
        self.cid = (qs.get("cid", [None])[0] or self.channel_name)[:64]

        room = await self.get_room()
        if not room:
            room = self._fresh_room()

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        if self.cid in room["players"]:
            room["players"][self.cid]["channel"] = self.channel_name
        else:
            taken = {p["num"] for p in room["players"].values()}
            num = 1 if 1 not in taken else (2 if 2 not in taken else 0)  # 0 = spectator
            room["players"][self.cid] = {
                "name": f"Joueur {num}" if num else "Spectateur",
                "num": num,
                "channel": self.channel_name,
            }
        if not room["host"] or room["host"] not in room["players"]:
            room["host"] = self.cid

        await self.save_room(room)
        await self.accept()
        await self.broadcast_state()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        room = await self.get_room()
        if not room:
            return
        player = room["players"].get(self.cid)
        if player and player.get("channel") == self.channel_name:
            del room["players"][self.cid]
            if not room["players"]:
                await state_adapter.delete_state(f"quizwho_room_{self.room_code}")
                return
            await self.save_room(room)
            await self.broadcast_state()

    # ── Receive ─────────────────────────────────────────────────────────────
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")
        room = await self.get_room()
        if not room or self.cid not in room["players"]:
            return
        me = room["players"][self.cid]
        is_host = self.cid == room["host"]

        if action == "set_name":
            me["name"] = (data.get("name") or me["name"])[:20]
        elif action == "set_settings" and is_host:
            mt = data.get("media_type")
            if mt in UNIVERSES:
                room["media_type"] = mt
            d = data.get("difficulty")
            if d in DIFFICULTIES:
                room["difficulty"] = d
        elif action == "start_game" and is_host:
            await self.start_game(room)
            return
        elif action == "ask":
            await self.handle_ask(room, me, data.get("attribute"))
            return
        elif action == "guess":
            await self.handle_guess(room, me, str(data.get("guess_id", "")))
            return
        elif action == "chat":
            text = (data.get("message") or "").strip()[:120]
            if text:
                room["messages"].append({"user": me["name"], "text": text})
                room["messages"] = room["messages"][-100:]
        elif action == "back_to_lobby" and is_host:
            room.update(
                {
                    "state": "lobby",
                    "board": [],
                    "questions": [],
                    "secrets": {},
                    "eliminated": {"1": [], "2": []},
                    "turn": 1,
                    "last_answer": None,
                    "winner": None,
                }
            )
        else:
            return

        await self.save_room(room)
        await self.broadcast_state()

    def _nums_present(self, room):
        return {p["num"] for p in room["players"].values() if p["num"] in (1, 2)}

    async def start_game(self, room):
        if self._nums_present(room) != {1, 2}:
            self._system(room, "Il faut 2 joueurs pour lancer.")
            await self.save_room(room)
            await self.broadcast_state()
            return
        board, questions = await sync_to_async(_build_board)(
            room["media_type"], room["difficulty"]
        )
        if len(board) < 8 or not questions:
            self._system(room, "Pas assez de personnages pour cet univers.")
            await self.save_room(room)
            await self.broadcast_state()
            return
        ids = [b["id"] for b in board]
        secret1 = random.choice(ids)
        secret2 = random.choice([i for i in ids if i != secret1] or ids)
        room.update(
            {
                "board": board,
                "questions": questions,
                "secrets": {"1": secret1, "2": secret2},
                "eliminated": {"1": [], "2": []},
                "turn": 1,
                "last_answer": None,
                "winner": None,
                "state": "playing",
                "messages": [],
            }
        )
        self._system(room, "La partie commence ! Au joueur 1 de poser une question.")
        await self.save_room(room)
        await self.broadcast_state()

    async def handle_ask(self, room, me, attribute):
        num = me["num"]
        if room["state"] != "playing" or room["winner"] or room["turn"] != num:
            return
        if attribute not in {q["attr"] for q in room["questions"]}:
            return
        target = room["secrets"].get("2" if num == 1 else "1")
        result = await sync_to_async(_resolve_ask)(
            room["media_type"],
            attribute,
            target,
            room["board"],
            room["eliminated"][str(num)],
        )
        secret_has, new_elim = result
        if secret_has is None:
            return
        room["eliminated"][str(num)] = new_elim
        label = next(
            (q["label"] for q in room["questions"] if q["attr"] == attribute), attribute
        )
        room["last_answer"] = {
            "by": num,
            "name": me["name"],
            "label": label,
            "answer": "OUI" if secret_has else "NON",
        }
        room["turn"] = 2 if num == 1 else 1
        await self.save_room(room)
        await self.broadcast_state()

    async def handle_guess(self, room, me, guess_id):
        num = me["num"]
        if room["state"] != "playing" or room["winner"] or room["turn"] != num:
            return
        target = str(room["secrets"].get("2" if num == 1 else "1"))
        if guess_id == target:
            room["winner"] = num
            room["state"] = "ended"
            room["last_answer"] = {
                "by": num,
                "name": me["name"],
                "label": "Accusation",
                "answer": "GAGNÉ",
            }
            self._system(room, f"{me['name']} a démasqué l'adversaire — victoire !")
        else:
            elim = set(room["eliminated"][str(num)])
            elim.add(guess_id)
            room["eliminated"][str(num)] = list(elim)
            room["last_answer"] = {
                "by": num,
                "name": me["name"],
                "label": "Accusation",
                "answer": "RATÉ",
            }
            room["turn"] = 2 if num == 1 else 1
        await self.save_room(room)
        await self.broadcast_state()

    def _system(self, room, text):
        room["messages"].append({"user": "", "text": text, "is_system": True})

    # ── Broadcast ───────────────────────────────────────────────────────────
    async def broadcast_chat(self, msg):  # unused (chat is in state) but kept for base
        pass

    async def broadcast_state(self):
        room = await self.get_room()
        if not room:
            return
        by_id = {b["id"]: b for b in room["board"]}
        ended = room["state"] == "ended"
        players_public = [
            {
                "num": p["num"],
                "name": p["name"],
                "is_host": cid == room["host"],
            }
            for cid, p in room["players"].items()
            if p["num"] in (1, 2)
        ]
        opponent_joined = self._nums_present(room) == {1, 2}
        for cid, p in room["players"].items():
            num = p["num"]
            my_secret = room["secrets"].get(str(num)) if num else None
            payload = {
                "type": "state",
                "room": {
                    "state": room["state"],
                    "media_type": room["media_type"],
                    "difficulty": room["difficulty"],
                    "board": room["board"],
                    "questions": room["questions"],
                    "turn": room["turn"],
                    "last_answer": room["last_answer"],
                    "winner": room["winner"],
                    "players": players_public,
                    "opponent_joined": opponent_joined,
                    "messages": room.get("messages", []),
                },
                "your_num": num,
                "your_name": p["name"],
                "is_host": cid == room["host"],
                "your_secret_id": my_secret,
                "your_secret_title": (by_id.get(my_secret) or {}).get("title"),
                "your_eliminated": room["eliminated"].get(str(num), []) if num else [],
                "your_turn": (
                    room["state"] == "playing"
                    and not room["winner"]
                    and opponent_joined
                    and room["turn"] == num
                ),
                "you_won": ended and room["winner"] == num,
            }
            await self.channel_layer.send(
                p["channel"], {"type": "send_msg", "message": payload}
            )
