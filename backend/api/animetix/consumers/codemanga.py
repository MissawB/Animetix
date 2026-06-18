import json
import random
from asgiref.sync import sync_to_async
from .base import BaseConsumer, state_adapter
from ..containers import get_container


class CodeMangaConsumer(BaseConsumer):
    async def get_room(self):
        return await state_adapter.get_state(f"codemanga_room_{self.room_code}")

    async def save_room(self, room):
        await state_adapter.set_state(
            f"codemanga_room_{self.room_code}", room, timeout=3600
        )

    async def connect(self):
        self.room_code = self.scope["url_route"]["kwargs"]["room_code"].upper()
        self.room_group_name = f"codemanga_{self.room_code}"
        room = await self.get_room()
        if not room:
            room = {
                "host": self.channel_name,
                "players": {},
                "state": "lobby",
                "grid": [],
                "turn": "blue",
                "blue_score": 0,
                "red_score": 0,
                "winner": None,
            }
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        room["players"][self.channel_name] = {
            "name": f"Fan #{random.randint(100, 999)}",
            "team": None,
            "role": None,
        }
        await self.save_room(room)
        await self.accept()
        await self.broadcast_state()

    async def receive(self, text_data):
        data = json.loads(text_data)
        action, room = data.get("action"), await self.get_room()
        if not room:
            return
        if action == "set_player":
            room["players"][self.channel_name].update(
                {
                    "name": data.get("name", "Anonyme"),
                    "team": data.get("team", "blue"),
                    "role": data.get("role", "operative"),
                }
            )
        elif action == "start_game":
            await self.generate_grid(room)
            room["state"] = "playing"
            await self.save_room(room)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "send_msg",
                    "message": {
                        "type": "redirect",
                        "url": f"/codemanga/game/{self.room_code}/",
                    },
                },
            )
        elif action == "click_card":
            await self.handle_card_click(room, data.get("index"))
        await self.save_room(room)
        await self.broadcast_state()

    async def generate_grid(self, room):
        data = await sync_to_async(get_container().catalog_service.load_data)("Anime")
        if not data:
            return
        selected = random.sample(list(data["db"]), 25)
        roles = (["blue"] * 9) + (["red"] * 8) + (["neutral"] * 7) + (["assassin"] * 1)
        random.shuffle(roles)
        room["grid"] = [
            {
                "title": selected[i].get("title"),
                "image": selected[i].get("image"),
                "role": roles[i],
                "revealed": False,
            }
            for i in range(25)
        ]
        room["blue_score"], room["red_score"], room["turn"], room["winner"] = (
            0,
            0,
            "blue",
            None,
        )

    async def handle_card_click(self, room, idx):
        if room["state"] != "playing" or room["winner"]:
            return
        card = room["grid"][idx]
        if card["revealed"]:
            return
        card["revealed"] = True
        if card["role"] == "assassin":
            room["winner"] = "red" if room["turn"] == "blue" else "blue"
        elif card["role"] != room["turn"]:
            room["turn"] = "red" if room["turn"] == "blue" else "blue"
        room["blue_score"] = sum(
            1 for c in room["grid"] if c["role"] == "blue" and c["revealed"]
        )
        room["red_score"] = sum(
            1 for c in room["grid"] if c["role"] == "red" and c["revealed"]
        )
        if room["blue_score"] == 9:
            room["winner"] = "blue"
        if room["red_score"] == 8:
            room["winner"] = "red"

    async def broadcast_state(self):
        room = await self.get_room()
        if not room:
            return
        public_grid = [
            {
                "title": c["title"],
                "image": c["image"],
                "revealed": c["revealed"],
                "role": (c["role"] if c["revealed"] else "unknown"),
            }
            for c in room["grid"]
        ]
        for ch, p in room["players"].items():
            grid_to_send = room["grid"] if p["role"] == "spymaster" else public_grid
            await self.channel_layer.send(
                ch,
                {
                    "type": "send_msg",
                    "message": {
                        "type": "state",
                        "room": {
                            "state": room["state"],
                            "grid": grid_to_send,
                            "turn": room["turn"],
                            "blue_score": room["blue_score"],
                            "red_score": room["red_score"],
                            "winner": room["winner"],
                            "players": list(room["players"].values()),
                        },
                        "my_role": p["role"],
                        "my_team": p["team"],
                    },
                },
            )
