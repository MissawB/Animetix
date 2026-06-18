import json
from asgiref.sync import sync_to_async
from .base import BaseConsumer, state_adapter
from ..containers import get_container
from ..services import DIFFICULTY_SETTINGS


class UndercoverConsumer(BaseConsumer):
    async def get_room(self):
        room = await state_adapter.get_state(f"undercover_room_{self.room_code}")
        return room

    async def save_room(self, room):
        await state_adapter.set_state(
            f"undercover_room_{self.room_code}", room, timeout=3600
        )

    async def connect(self):
        self.room_code = self.scope["url_route"]["kwargs"]["room_code"].upper()
        self.room_group_name = f"undercover_{self.room_code}"

        room = await self.get_room()
        if not room:
            room = {
                "host": self.channel_name,
                "players": {},
                "state": "lobby",
                "messages": [],
                "clue": "",
                "media_type": "Anime",
                "difficulty": "Normal",
                "votes": {},
            }

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        room["players"][self.channel_name] = {
            "name": f"Player {len(room['players']) + 1}",
            "role": None,
            "word": None,
            "image": None,
            "is_host": (self.channel_name == room["host"]),
        }

        await self.save_room(room)
        await self.accept()
        await self.broadcast_state()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        room = await self.get_room()
        if room and self.channel_name in room["players"]:
            del room["players"][self.channel_name]
            if not room["players"]:
                await state_adapter.delete_state(f"undercover_room_{self.room_code}")
            elif room["host"] == self.channel_name:
                new_host = list(room["players"].keys())[0]
                room["host"] = new_host
                room["players"][new_host]["is_host"] = True
                await self.save_room(room)
            else:
                await self.save_room(room)
            await self.broadcast_state()

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")
        room = await self.get_room()
        if not room:
            return

        if action == "set_name":
            room["players"][self.channel_name]["name"] = data.get("name", "")[:15]
            await self.save_room(room)
            await self.broadcast_state()
        elif action == "set_settings" and self.channel_name == room["host"]:
            room["media_type"] = data.get("media_type", "Anime")
            room["difficulty"] = data.get("difficulty", "Normal")
            await self.save_room(room)
            await self.broadcast_state()
        elif action == "chat":
            msg = {
                "user": room["players"][self.channel_name]["name"],
                "text": data.get("message", "")[:100],
                "is_system": False,
            }
            room["messages"].append(msg)
            await self.save_room(room)
            await self.broadcast_chat(msg)
        elif action == "start_game" and self.channel_name == room["host"]:
            await self.start_game_logic(room)
        elif action == "vote":
            room["votes"][self.channel_name] = data.get("voted_for")
            await self.save_room(room)
            await self.broadcast_state()
        elif action == "reveal" and self.channel_name == room["host"]:
            room["state"] = "revealed"
            await self.save_room(room)
            await self.broadcast_state()
        elif action == "back_to_lobby" and self.channel_name == room["host"]:
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
        players_list = [
            {
                "id": ch,
                "name": p["name"],
                "is_host": p["is_host"],
                "has_voted": ch in room["votes"],
            }
            for ch, p in room["players"].items()
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
                    "media_type": room["media_type"],
                },
            },
        )
        if room["state"] in ["playing", "revealed"]:
            for ch, p in room["players"].items():
                await self.channel_layer.send(
                    ch,
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
        game_data = await sync_to_async(container.game_service.start_undercover_game)(
            media_type=room["media_type"],
            difficulty=room["difficulty"],
            player_ids=list(room["players"].keys()),
            rank_limits=DIFFICULTY_SETTINGS,
        )
        if not game_data:
            return

        clue = (
            await sync_to_async(container.llm_service.generate_undercover_clue)(
                room["media_type"],
                game_data["civil_word"],
                game_data["undercover_word"],
            )
            or "Mystère..."
        )

        for ch, p in room["players"].items():
            assignment = game_data["assignments"][ch]
            p["role"], p["word"], p["image"] = (
                assignment["role"],
                assignment["word"],
                assignment["image"],
            )
        room["clue"], room["state"] = clue, "playing"
        await self.save_room(room)
        await self.broadcast_state()
