import json
import re
import unicodedata
from difflib import SequenceMatcher
from urllib.parse import parse_qs

from animetix_project.logging_config import get_logger
from asgiref.sync import sync_to_async

from ..containers import get_container
from ..services import DIFFICULTY_SETTINGS
from .base import BaseConsumer, state_adapter

logger = get_logger("animetix." + __name__)

KNOWN_CATS = {"Anime", "Manga", "Character", "Movie", "Game", "Actor", "VGChar"}
# Cache key holding the list of known room codes — public ones are surfaced in
# the lobby listing (the cache can't enumerate keys, so we keep our own index).
INDEX_KEY = "undercover_room_index"


# Threats = undercovers + Mr. Whites. Capped so civils keep a strict majority at
# the start (otherwise the game could open already at parity).
def _max_threats(n_players):
    return max(1, (n_players - 1) // 2)


def _norm_guess(text):
    """Loose normalisation so a Mr. White guess matches despite case/accents/punct."""
    folded = unicodedata.normalize("NFKD", str(text or ""))
    folded = folded.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "", folded)


def _guess_words(text):
    """Significant words (accent-folded, tiny words dropped) of a title/guess."""
    folded = unicodedata.normalize("NFKD", str(text or ""))
    folded = folded.encode("ascii", "ignore").decode("ascii").lower()
    return [w for w in re.findall(r"[a-z0-9]+", folded) if len(w) > 2]


def _guess_matches(guess, target):
    """Tolerant match for a Mr. White guess: accepts typos, casing, accents,
    word order and a missing subtitle — the name doesn't have to be perfect."""
    g, t = _norm_guess(guess), _norm_guess(target)
    if not g or not t:
        return False
    if g == t:
        return True
    # Typo tolerance on the whole compact string.
    if SequenceMatcher(None, g, t).ratio() >= 0.8:
        return True
    # Word-level tolerance: every guessed word lands (fuzzily) in the title and
    # together they cover at least half of the title's significant words.
    gw, tw = _guess_words(guess), _guess_words(target)
    if not gw or not tw:
        return False

    def near(a, b):
        return a == b or SequenceMatcher(None, a, b).ratio() >= 0.8

    matched_g = sum(1 for a in gw if any(near(a, b) for b in tw))
    matched_t = sum(1 for b in tw if any(near(a, b) for a in gw))
    return matched_g == len(gw) and matched_t >= max(1, (len(tw) + 1) // 2)


class UndercoverConsumer(BaseConsumer):
    """Players are keyed by a stable client id (cid) sent as a query param, NOT by the
    ephemeral channel name — so a page refresh reuses the same slot (and keeps the
    host) instead of spawning a new player every time.

    In-game the round loops: living players vote, the most-voted is eliminated
    (tie → revote), their role is revealed; a Mr. White then gets one guess at the
    civils' word. Civils win when every threat (intrus + Mr. White) is out; the
    threats win on reaching parity; a Mr. White also wins alone by guessing right or
    surviving to parity."""

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
        created = not room
        if created:
            room = self._fresh_room()
            # The creator's URL may carry the chosen visibility (public/private).
            if qs.get("visibility", [None])[0] == "public":
                room["visibility"] = "public"

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
                "alive": True,
                "channel": self.channel_name,
            }

        # Assign the host if the slot is vacant (first player, or the host left).
        if not room["host"] or room["host"] not in room["players"]:
            room["host"] = self.cid

        await self.save_room(room)
        await self._index_add()
        await self.accept()
        await self.broadcast_state()

    def _fresh_room(self):
        return {
            "host": None,
            "players": {},
            "state": "lobby",
            "messages": [],
            "name": "",
            "visibility": "private",
            "categories": ["Anime"],
            "difficulty": "Normal",
            "num_undercovers": 1,
            "num_mrwhites": 0,
            "votes": {},
            "round": 0,
            "civil_word": "",
            "undercover_word": "",
            "pending_white": None,
            "result": None,
        }

    async def _index_add(self):
        """Register this room code so the public listing can find it."""
        try:
            codes = await state_adapter.get_state(INDEX_KEY) or []
            if self.room_code not in codes:
                codes.append(self.room_code)
                await state_adapter.set_state(INDEX_KEY, codes, timeout=86400)
        except Exception:
            # Best-effort: the room stays joinable via its code even if the
            # public-lobby listing misses it — but that degradation must be visible.
            logger.warning(
                "Failed to register room %s in the public lobby index",
                self.room_code,
                exc_info=True,
            )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        room = await self.get_room()
        if not room:
            return
        player = room["players"].get(self.cid)
        # Only drop the player if this is still their active connection — a refresh
        # often reconnects (updating the channel) before the old socket's disconnect
        # fires, and we must not remove the just-reconnected player.
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
            cats = [c for c in (data.get("categories") or []) if c in KNOWN_CATS]
            room["categories"] = cats or ["Anime"]
            room["difficulty"] = data.get("difficulty", "Normal")
            room["num_undercovers"] = self._as_int(
                data.get("num_undercovers"), 1, 1, 12
            )
            room["num_mrwhites"] = self._as_int(data.get("num_mrwhites"), 0, 0, 12)
            if data.get("visibility") in ("public", "private"):
                room["visibility"] = data["visibility"]
            if isinstance(data.get("name"), str):
                room["name"] = data["name"][:24]
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
            await self.handle_vote(room, data.get("voted_for"))
        elif action == "mrwhite_guess":
            await self.handle_mrwhite_guess(room, data.get("guess"))
        elif action == "back_to_lobby" and is_host:
            self._reset_to_lobby(room)
            await self.save_room(room)
            await self.broadcast_state()

    @staticmethod
    def _as_int(value, default, lo, hi):
        try:
            return max(lo, min(int(value), hi))
        except (TypeError, ValueError):
            return default

    def _reset_to_lobby(self, room):
        room["state"] = "lobby"
        room["votes"], room["messages"] = {}, []
        room["round"] = 0
        room["pending_white"] = None
        room["result"] = None
        room["civil_word"] = room["undercover_word"] = ""
        for p in room["players"].values():
            p["role"], p["word"], p["image"], p["alive"] = None, None, None, True

    # ── Voting / elimination loop ───────────────────────────────────────────
    async def handle_vote(self, room, target):
        if room["state"] != "playing":
            return
        voter = room["players"].get(self.cid)
        tgt = room["players"].get(target)
        if not voter or not voter.get("alive") or target == self.cid:
            return
        if not tgt or not tgt.get("alive"):
            return
        room["votes"][self.cid] = target

        living = [cid for cid, p in room["players"].items() if p.get("alive")]
        if living and all(cid in room["votes"] for cid in living):
            await self.resolve_votes(room)
        else:
            await self.save_room(room)
            await self.broadcast_state()

    async def resolve_votes(self, room):
        living = {cid for cid, p in room["players"].items() if p.get("alive")}
        tally = {}
        for tgt in room["votes"].values():
            if tgt in living:
                tally[tgt] = tally.get(tgt, 0) + 1
        room["votes"] = {}
        if not tally:
            await self.save_room(room)
            await self.broadcast_state()
            return

        top = max(tally.values())
        leaders = [cid for cid, c in tally.items() if c == top]
        if len(leaders) > 1:
            # Égalité : personne n'est éliminé, on relance un vote.
            self._system(room, "Égalité des votes — personne n'est éliminé, on revote.")
            await self.save_room(room)
            await self.broadcast_state()
            return

        victim_id = leaders[0]
        victim = room["players"][victim_id]
        victim["alive"] = False
        role_label = {
            "Undercover": "Intrus",
            "MrWhite": "Mr. White",
            "Civil": "Civil",
        }.get(victim["role"], victim["role"])
        self._system(room, f"{victim['name']} est éliminé — c'était un {role_label}.")

        if victim["role"] == "MrWhite":
            # Un Mr. White éliminé tente de deviner le mot des civils (1 essai).
            room["state"] = "mrwhite_guess"
            room["pending_white"] = victim_id
            await self.save_room(room)
            await self.broadcast_state()
            return

        if not self._check_win(room):
            room["round"] += 1
        await self.save_room(room)
        await self.broadcast_state()

    async def handle_mrwhite_guess(self, room, guess):
        if room["state"] != "mrwhite_guess" or room["pending_white"] != self.cid:
            return
        white = room["players"][self.cid]
        room["pending_white"] = None
        if _guess_matches(guess, room["civil_word"]):
            self._system(
                room,
                f"{white['name']} (Mr. White) a deviné « {room['civil_word']} » — "
                f"Mr. White l'emporte !",
            )
            room["state"] = "ended"
            room["result"] = {
                "winner": "mrwhite",
                "reason": "guess",
                "mrwhite_winners": [white["name"]],
            }
        else:
            said = (guess or "").strip() or "—"
            self._system(
                room, f"{white['name']} (Mr. White) s'est trompé (« {said} »)."
            )
            room["state"] = "playing"
            if not self._check_win(room):
                room["round"] += 1
        await self.save_room(room)
        await self.broadcast_state()

    def _check_win(self, room):
        """Returns True and sets room['result']/state='ended' if the game is over."""
        threats = [
            p
            for p in room["players"].values()
            if p.get("alive") and p["role"] in ("Undercover", "MrWhite")
        ]
        civils = [
            p
            for p in room["players"].values()
            if p.get("alive") and p["role"] == "Civil"
        ]
        if not threats:
            room["state"] = "ended"
            room["result"] = {"winner": "civils", "reason": "all_threats_out"}
            self._system(room, "Tous les intrus sont démasqués — les Civils gagnent !")
            return True
        if len(threats) >= len(civils):
            whites = [p["name"] for p in threats if p["role"] == "MrWhite"]
            room["state"] = "ended"
            room["result"] = {
                "winner": "infiltres",
                "reason": "parity",
                "mrwhite_winners": whites,
            }
            self._system(
                room, "Les intrus atteignent la parité — les infiltrés gagnent !"
            )
            return True
        return False

    def _system(self, room, text):
        room["messages"].append({"user": "", "text": text, "is_system": True})

    # ── Broadcast ───────────────────────────────────────────────────────────
    async def broadcast_chat(self, msg):
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "send_msg", "message": {"type": "chat_message", "message": msg}},
        )

    async def broadcast_state(self):
        room = await self.get_room()
        if not room:
            return
        ended = room["state"] == "ended"
        pending = room.get("pending_white")
        players_list = []
        for cid, p in room["players"].items():
            alive = p.get("alive", True)
            entry = {
                "id": cid,
                "name": p["name"],
                "is_host": cid == room["host"],
                "alive": alive,
                "has_voted": cid in room["votes"],
            }
            # Eliminated players are revealed to all; living roles stay hidden
            # until the game ends.
            if ended or not alive:
                entry.update(
                    {"role": p["role"], "word": p["word"], "image": p["image"]}
                )
            players_list.append(entry)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "send_msg",
                "message": {
                    "type": "room_state",
                    "state": room["state"],
                    "players": players_list,
                    "messages": room["messages"],
                    "difficulty": room["difficulty"],
                    "visibility": room.get("visibility", "private"),
                    "name": room.get("name", ""),
                    "categories": room.get("categories", ["Anime"]),
                    "num_undercovers": room.get("num_undercovers", 1),
                    "num_mrwhites": room.get("num_mrwhites", 0),
                    "round": room.get("round", 0),
                    "pending_white": pending,
                    "pending_white_name": (
                        room["players"][pending]["name"]
                        if pending and pending in room["players"]
                        else None
                    ),
                    "result": room.get("result"),
                    "civil_word": room["civil_word"] if ended else "",
                    "undercover_word": room["undercover_word"] if ended else "",
                },
            },
        )
        if room["state"] in ("playing", "mrwhite_guess", "ended"):
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
        max_threats = _max_threats(n_players)
        num_undercovers = max(1, min(room.get("num_undercovers", 1), max_threats))
        num_mrwhites = max(
            0, min(room.get("num_mrwhites", 0), max_threats - num_undercovers)
        )
        categories = room.get("categories", ["Anime"])
        game_data = await sync_to_async(game_service.start_undercover_game)(
            categories=categories,
            difficulty=room["difficulty"],
            player_ids=list(room["players"].keys()),
            rank_limits=DIFFICULTY_SETTINGS,
            num_undercovers=num_undercovers,
            num_mrwhites=num_mrwhites,
        )
        if not game_data:
            return

        for cid, p in room["players"].items():
            assignment = game_data["assignments"][cid]
            p["role"], p["word"], p["image"] = (
                assignment["role"],
                assignment["word"],
                assignment["image"],
            )
            p["alive"] = True
        room["civil_word"] = game_data["civil_word"]
        room["undercover_word"] = game_data["undercover_word"]
        room["votes"] = {}
        room["round"] = 1
        room["pending_white"] = None
        room["result"] = None
        room["messages"] = []
        self._system(
            room,
            "La partie commence ! Décrivez votre mot à tour de rôle, puis votez.",
        )
        room["state"] = "playing"
        await self.save_room(room)
        await self.broadcast_state()
