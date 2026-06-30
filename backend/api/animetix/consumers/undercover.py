import json
from urllib.parse import parse_qs

from asgiref.sync import sync_to_async

from ..containers import get_container
from ..services import DIFFICULTY_SETTINGS
from .base import BaseConsumer, state_adapter


class UndercoverConsumer(BaseConsumer):
    """Players are keyed by a stable client id (cid) sent as a query param, NOT by the
    ephemeral channel name — so a page refresh reuses the same slot (and keeps the
    host) instead of spawning a new player every time."""

    async def get_room(self):
        return await state_adapter.get_state(f"undercover_room_{self.room_code}")

    async def save_room(self, room):
        await state_adapter.set_state(
            f"undercover_room_{self.room_code}", room, timeout=3600
        )

    async def connect(self):
        self.room_code = self.scope["url_route"]["kwargs"]["room_code"].upper()
        self.room_group_name = f"undercover_{self.room_code}"
        qs = parse_qs(self.scope.get("query_string", b"").decode())
        self.cid = (qs.get("cid", [None])[0] or self.channel_name)[:64]

        room = await self.get_room()
        if not room:
            room = {
                "host": None,
                "players": {},
                "state": "lobby",
                "messages": [],
                "clue": "",
                "categories": ["Anime"],
                "difficulty": "Normal",
                "num_undercovers": 1,
                "votes": {},
            }

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        if self.cid in room["players"]:
            # Reconnect: keep the player's slot/name, just point at the new channel.
            room["players"][self.cid]["channel"] = self.channel_name
        else:
            room["players"][self.cid] = {
                "name": f"Agent {len(room['players']) + 1}",
                "role": None,
                "word": None,
                "image": None,
                "channel": self.channel_name,
            }

        # Assign the host if the slot is vacant (first player, or the host left).
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
        # Only drop the player if this is still their active connection — a refresh
        # often reconnects (updating the channel) before the old socket's disconnect
        # fires, and we must not remove the just-reconnected player. The host slot is
        # left as-is so a refreshing host keeps it on reconnect.
        if player and player.get("channel") == self.channel_name:
            del room["players"][self.cid]
            if not room["players"]:
                await state_adapter.delete_state(f"undercover_room_{self.room_code}")
                return
            await self.save_room(room)
            await self.broadcast_state()

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")
        room = await self.get_room()
        if not room or self.cid not in room["players"]:
            return
        is_host = self.cid == room["host"]

        if action == "set_name":
            room["players"][self.cid]["name"] = (data.get("name", "") or "")[:15]
            await self.save_room(room)
            await self.broadcast_state()
        elif action == "set_settings" and is_host:
            known = {"Anime", "Manga", "Character", "Movie", "Game", "Actor", "VGChar"}
            cats = [c for c in (data.get("categories") or []) if c in known]
            room["categories"] = cats or ["Anime"]
            room["difficulty"] = data.get("difficulty", "Normal")
            try:
                room["num_undercovers"] = max(
                    1, min(int(data.get("num_undercovers", 1)), 3)
                )
            except (TypeError, ValueError):
                room["num_undercovers"] = 1
            await self.save_room(room)
            await self.broadcast_state()
        elif action == "chat":
            msg = {
                "user": room["players"][self.cid]["name"],
                "text": (data.get("message", "") or "")[:100],
                "is_system": False,
            }
            room["messages"].append(msg)
            await self.save_room(room)
            await self.broadcast_chat(msg)
        elif action == "start_game" and is_host:
            await self.start_game_logic(room)
        elif action == "vote":
            room["votes"][self.cid] = data.get("voted_for")
            await self.save_room(room)
            await self.broadcast_state()
        elif action == "reveal" and is_host:
            room["state"] = "revealed"
            await self.save_room(room)
            await self.broadcast_state()
        elif action == "back_to_lobby" and is_host:
            room["state"] = "lobby"
            room["votes"], room["messages"] = {}, []
            for p in room["players"].values():
                p["role"], p["word"], p["image"] = None, None, None
            await self.save_room(room)
            await self.broadcast_state()

    async def broadcast_chat(self, msg):
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "send_msg", "message": {"type": "chat_message", "message": msg}},
        )

    async def broadcast_state(self):
        room = await self.get_room()
        if not room:
            return
        revealed = room["state"] == "revealed"
        players_list = [
            {
                "id": cid,
                "name": p["name"],
                "is_host": cid == room["host"],
                "has_voted": cid in room["votes"],
                # Roles/words are only exposed to everyone once the round is revealed.
                **(
                    {"role": p["role"], "word": p["word"], "image": p["image"]}
                    if revealed
                    else {}
                ),
            }
            for cid, p in room["players"].items()
        ]
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "send_msg",
                "message": {
                    "type": "room_state",
                    "state": room["state"],
                    "players": players_list,
                    "clue": room["clue"],
                    "messages": room["messages"],
                    "difficulty": room["difficulty"],
                    "categories": room.get("categories", ["Anime"]),
                    "num_undercovers": room.get("num_undercovers", 1),
                    "votes": room["votes"] if revealed else {},
                },
            },
        )
        if room["state"] in ["playing", "revealed"]:
            for p in room["players"].values():
                await self.channel_layer.send(
                    p["channel"],
                    {
                        "type": "send_msg",
                        "message": {
                            "type": "private_role",
                            "role": p["role"],
                            "word": p["word"],
                            "image": p["image"],
                        },
                    },
                )

    async def start_game_logic(self, room):
        container = get_container()
        game_service = container.core.game_service()
        n_players = len(room["players"])
        # Keep at least 2 civils so the round stays playable.
        num_undercovers = max(
            1, min(room.get("num_undercovers", 1), max(1, n_players - 2))
        )
        categories = room.get("categories", ["Anime"])
        game_data = await sync_to_async(game_service.start_undercover_game)(
            categories=categories,
            difficulty=room["difficulty"],
            player_ids=list(room["players"].keys()),
            rank_limits=DIFFICULTY_SETTINGS,
            num_undercovers=num_undercovers,
        )
        if not game_data:
            return

        # No LLM clue here on purpose: Undercover is a CPU / no-login game and
        # must never hit the GPU inference stack (which is Berrix-gated and would
        # also stall the round start). Players describe their own word instead.
        clue = ""

        for cid, p in room["players"].items():
            assignment = game_data["assignments"][cid]
            p["role"], p["word"], p["image"] = (
                assignment["role"],
                assignment["word"],
                assignment["image"],
            )
        room["clue"], room["state"] = clue, "playing"
        await self.save_room(room)
        await self.broadcast_state()
