import json
import os
import random
from urllib.parse import parse_qs

from asgiref.sync import sync_to_async

from ..containers import get_container
from .base import BaseConsumer, state_adapter

# Board composition (Codenames): the starting team (blue) gets 9, the other 8.
BLUE_CARDS, RED_CARDS, NEUTRAL_CARDS = 9, 8, 7
# Same card universes as Undercover — the host ticks any mix of these.
KNOWN_CATS = {"Anime", "Manga", "Character", "Movie", "Game", "Actor", "VGChar"}
# Video-game characters have no catalog collection; their cards live in a file.
VG_CHAR_FILE = ("data", "artifacts", "vg_char_data_for_lookup.json")
# Difficulty = required anime/manga knowledge: how deep into the popularity-ranked
# catalog we draw cards from (Easy = only very famous works, Hard = deep cuts).
DIFFICULTY_LIMITS = {"Easy": 150, "Normal": 450, "Hard": 1200}


class CodeMangaConsumer(BaseConsumer):
    """Codenames-style game on anime/manga cards. Players are keyed by a stable
    client id (cid) sent as a query param — a refresh reuses the same slot (and
    keeps the host) instead of spawning a duplicate. Spymasters see every card's
    team; operatives see a masked grid and click after their spymaster's clue."""

    async def get_room(self):
        return await state_adapter.get_state(f"codemanga_room_{self.room_code}")

    async def save_room(self, room):
        await state_adapter.set_state(
            f"codemanga_room_{self.room_code}", room, timeout=3600
        )

    def _fresh_room(self):
        return {
            "host": None,
            "players": {},
            "state": "lobby",
            "categories": ["Anime"],
            "difficulty": "Normal",
            "grid": [],
            "turn": "blue",
            "blue_score": 0,
            "red_score": 0,
            "winner": None,
            "clue": None,
            "messages": [],
        }

    async def connect(self):
        self.room_code = self.scope["url_route"]["kwargs"]["room_code"].upper()
        self.room_group_name = f"codemanga_{self.room_code}"
        qs = parse_qs(self.scope.get("query_string", b"").decode())
        self.cid = (qs.get("cid", [None])[0] or self.channel_name)[:64]

        room = await self.get_room()
        if not room:
            room = self._fresh_room()

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        if self.cid in room["players"]:
            room["players"][self.cid]["channel"] = self.channel_name
        else:
            room["players"][self.cid] = {
                "name": f"Fan #{random.randint(100, 999)}",
                "team": None,
                "role": None,
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
                await state_adapter.delete_state(f"codemanga_room_{self.room_code}")
                return
            await self.save_room(room)
            await self.broadcast_state()

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")
        room = await self.get_room()
        if not room or self.cid not in room["players"]:
            return
        me = room["players"][self.cid]
        is_host = self.cid == room["host"]

        if action == "set_player":
            me["name"] = (data.get("name") or me["name"])[:20]
            team = data.get("team")
            me["team"] = team if team in ("blue", "red") else me["team"]
            role = data.get("role")
            me["role"] = role if role in ("spymaster", "operative") else me["role"]
        elif action == "set_categories" and is_host:
            cats = [c for c in (data.get("categories") or []) if c in KNOWN_CATS]
            room["categories"] = cats or ["Anime"]
        elif action == "set_difficulty" and is_host:
            d = data.get("difficulty")
            room["difficulty"] = d if d in DIFFICULTY_LIMITS else "Normal"
        elif action == "start_game" and is_host:
            await self.generate_grid(room)
            if room["grid"]:
                room["state"] = "playing"
        elif action == "give_clue":
            self.handle_clue(room, me, data)
        elif action == "click_card":
            self.handle_card_click(room, me, data.get("index"))
        elif action == "chat":
            text = (data.get("message") or "").strip()[:120]
            if text:
                room["messages"].append({"user": me["name"], "text": text})
                room["messages"] = room["messages"][-100:]
        elif action == "back_to_lobby" and is_host:
            room.update(
                {
                    "state": "lobby",
                    "grid": [],
                    "winner": None,
                    "clue": None,
                    "blue_score": 0,
                    "red_score": 0,
                    "turn": "blue",
                }
            )
        else:
            return

        await self.save_room(room)
        await self.broadcast_state()

    # ── Game logic ──────────────────────────────────────────────────────────
    async def generate_grid(self, room):
        limit = DIFFICULTY_LIMITS.get(room.get("difficulty", "Normal"), 450)
        cards = await sync_to_async(self._collect_cards)(
            room.get("categories") or ["Anime"], limit
        )
        if len(cards) < 25:
            return
        selected = random.sample(cards, 25)
        roles = (
            ["blue"] * BLUE_CARDS
            + ["red"] * RED_CARDS
            + ["neutral"] * NEUTRAL_CARDS
            + ["assassin"]
        )
        random.shuffle(roles)
        room["grid"] = [
            {
                "title": selected[i]["title"],
                "image": selected[i]["image"],
                "role": roles[i],
                "revealed": False,
            }
            for i in range(25)
        ]
        room["blue_score"] = room["red_score"] = 0
        room["turn"], room["winner"], room["clue"] = "blue", None, None

    def _collect_cards(self, categories, limit=450):
        """Gather {title, image} cards from the selected categories (same data
        universes as Undercover), capped to the top-`limit` most popular of each
        so difficulty controls the required knowledge. Runs sync — call via
        sync_to_async."""
        catalog = get_container().catalog_service
        seen, out = set(), []
        for cat in categories:
            try:
                if cat == "VGChar":
                    items = self._load_vg_cards(catalog)
                else:
                    data = catalog.load_data(cat)
                    items = (data or {}).get("db", []) or []
            except Exception:
                items = []
            for it in items[:limit]:
                title = it.get("title") or it.get("name")
                image = it.get("image")
                if title and image and title not in seen:
                    seen.add(title)
                    out.append({"title": title, "image": image})
        return out

    def _load_vg_cards(self, catalog):
        root = getattr(getattr(catalog, "repository", None), "project_root", "") or ""
        path = os.path.join(root, *VG_CHAR_FILE)
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def handle_clue(self, room, me, data):
        """Current team's spymaster announces a one-word clue + a count."""
        if room["state"] != "playing" or room["winner"] or room.get("clue"):
            return
        if me["role"] != "spymaster" or me["team"] != room["turn"]:
            return
        word = (data.get("word") or "").strip()[:24]
        if not word:
            return
        try:
            number = max(1, min(int(data.get("number", 1)), 9))
        except (TypeError, ValueError):
            number = 1
        # A clue of N grants N+1 guesses (standard Codenames).
        room["clue"] = {
            "team": room["turn"],
            "word": word,
            "number": number,
            "guesses_left": number + 1,
        }

    def handle_card_click(self, room, me, idx):
        clue = room.get("clue")
        if room["state"] != "playing" or room["winner"] or not clue:
            return
        # Only the current team's operatives may guess, and only on their clue.
        if me["role"] != "operative" or me["team"] != room["turn"]:
            return
        if not isinstance(idx, int) or not (0 <= idx < len(room["grid"])):
            return
        card = room["grid"][idx]
        if card["revealed"]:
            return
        card["revealed"] = True
        clue["guesses_left"] -= 1

        if card["role"] == "assassin":
            room["winner"] = "red" if room["turn"] == "blue" else "blue"
            room["clue"] = None
            return

        room["blue_score"] = sum(
            1 for c in room["grid"] if c["role"] == "blue" and c["revealed"]
        )
        room["red_score"] = sum(
            1 for c in room["grid"] if c["role"] == "red" and c["revealed"]
        )
        if room["blue_score"] >= BLUE_CARDS:
            room["winner"] = "blue"
        elif room["red_score"] >= RED_CARDS:
            room["winner"] = "red"
        if room["winner"]:
            room["clue"] = None
            return

        # Wrong team / neutral ends the turn; a correct guess continues until the
        # granted guesses run out.
        if card["role"] != room["turn"] or clue["guesses_left"] <= 0:
            room["turn"] = "red" if room["turn"] == "blue" else "blue"
            room["clue"] = None

    # ── Broadcast ───────────────────────────────────────────────────────────
    async def broadcast_state(self):
        room = await self.get_room()
        if not room:
            return
        # Reveal every card's team in the lobby and once the game is decided.
        revealed = room["state"] != "playing" or bool(room["winner"])
        masked_grid = [
            {
                "title": c["title"],
                "image": c["image"],
                "revealed": c["revealed"],
                "role": c["role"] if (c["revealed"] or revealed) else "unknown",
            }
            for c in room["grid"]
        ]
        players_public = [
            {
                "id": cid,
                "name": p["name"],
                "team": p["team"],
                "role": p["role"],
                "is_host": cid == room["host"],
            }
            for cid, p in room["players"].items()
        ]
        for cid, p in room["players"].items():
            grid = room["grid"] if p["role"] == "spymaster" else masked_grid
            await self.channel_layer.send(
                p["channel"],
                {
                    "type": "send_msg",
                    "message": {
                        "type": "state",
                        "room": {
                            "state": room["state"],
                            "categories": room.get("categories", ["Anime"]),
                            "difficulty": room.get("difficulty", "Normal"),
                            "grid": grid,
                            "turn": room["turn"],
                            "blue_score": room["blue_score"],
                            "red_score": room["red_score"],
                            "winner": room["winner"],
                            "clue": room.get("clue"),
                            "messages": room.get("messages", []),
                            "players": players_public,
                        },
                        "my_role": p["role"],
                        "my_team": p["team"],
                        "my_id": cid,
                    },
                },
            )
