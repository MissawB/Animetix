"""Real-behavior tests for the CodeMangaConsumer (Codenames-style game).

Unit-style: the consumer is driven directly with the I/O boundaries mocked
(Channels layer, ``accept``) and persistence patched (``state_adapter`` + the
catalog ``get_container``). Players are keyed by a stable client id (cid) passed
as a ``?cid=`` query param. Asserts game logic + protocol, not bare mocks:
  * grid generation shape (25 cards) and role distribution (9/8/7/1),
  * clue gating: only the current team's spymaster may clue,
  * click rules require an active clue + a current-team operative,
  * turn switching, assassin loss, score-based wins, guess-limit end of turn,
  * spymaster vs operative grid visibility + per-player public shape.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from animetix.consumers import codemanga as cm

pytestmark = pytest.mark.asyncio


# --------------------------------------------------------------------------- #
# Helpers / fixtures
# --------------------------------------------------------------------------- #
def _make_consumer(room_code="abc", cid="cid-host", channel_name="chan-host"):
    c = cm.CodeMangaConsumer()
    c.room_code = room_code.upper()
    c.room_group_name = f"codemanga_{room_code.upper()}"
    c.cid = cid
    c.channel_name = channel_name
    c.scope = {
        "url_route": {"kwargs": {"room_code": room_code}},
        "query_string": f"cid={cid}".encode(),
    }
    c.send = AsyncMock()
    c.accept = AsyncMock()
    c.close = AsyncMock()
    c.channel_layer = AsyncMock()
    return c


def _fresh_room(host="cid-host"):
    return {
        "host": host,
        "players": {},
        "state": "lobby",
        "categories": ["Anime"],
        "grid": [],
        "turn": "blue",
        "blue_score": 0,
        "red_score": 0,
        "winner": None,
        "clue": None,
        "messages": [],
    }


def _playing_room_with_grid(host="cid-host"):
    """Mid-game room: indices 0-8 blue, 9-16 red, 17-23 neutral, 24 assassin.

    Blue's turn with an active blue clue granting plenty of guesses.
    """
    grid = []
    for i in range(25):
        role = (
            "blue"
            if i < 9
            else "red" if i < 17 else "neutral" if i < 24 else "assassin"
        )
        grid.append(
            {"title": f"T{i}", "image": f"i{i}.png", "role": role, "revealed": False}
        )
    room = _fresh_room(host)
    room.update(
        {
            "state": "playing",
            "grid": grid,
            "turn": "blue",
            "clue": {"team": "blue", "word": "ninja", "number": 5, "guesses_left": 6},
        }
    )
    room["players"] = {
        "cid-op": {
            "name": "Op",
            "team": "blue",
            "role": "operative",
            "channel": "chan-op",
        }
    }
    return room


def _blue_operative():
    return {"name": "Op", "team": "blue", "role": "operative", "channel": "chan-op"}


@pytest.fixture
def patched_state(mocker):
    store = {}

    async def _get(key):
        return store.get(key)

    async def _set(key, value, timeout=None):
        store[key] = value

    async def _del(key):
        store.pop(key, None)

    mocker.patch.object(cm.state_adapter, "get_state", side_effect=_get)
    mocker.patch.object(cm.state_adapter, "set_state", side_effect=_set)
    mocker.patch.object(cm.state_adapter, "delete_state", side_effect=_del)
    return store


@pytest.fixture
def patched_catalog(mocker):
    db = [{"title": f"Anime {i}", "image": f"img{i}.png"} for i in range(40)]
    catalog = MagicMock()
    catalog.load_data = MagicMock(return_value={"db": db})
    container = MagicMock()
    container.catalog_service = catalog
    mocker.patch.object(cm, "get_container", return_value=container)
    return catalog


# --------------------------------------------------------------------------- #
# connect (cid identity)
# --------------------------------------------------------------------------- #
async def test_connect_bootstraps_lobby_and_registers_player(patched_state, mocker):
    c = _make_consumer(cid="cid-host")
    mocker.patch.object(c, "broadcast_state", AsyncMock())
    await c.connect()

    assert c.room_code == "ABC"
    c.channel_layer.group_add.assert_awaited_once_with("codemanga_ABC", "chan-host")
    c.accept.assert_awaited_once()
    room = patched_state["codemanga_room_ABC"]
    assert room["state"] == "lobby"
    assert room["host"] == "cid-host"
    assert "cid-host" in room["players"]
    assert room["players"]["cid-host"]["name"].startswith("Fan #")


async def test_reconnect_same_cid_reuses_slot_and_keeps_host(patched_state, mocker):
    room = _fresh_room(host="cid-host")
    room["players"]["cid-host"] = {
        "name": "Kept",
        "team": "blue",
        "role": "spymaster",
        "channel": "old-chan",
    }
    patched_state["codemanga_room_ABC"] = room

    c = _make_consumer(cid="cid-host", channel_name="new-chan")
    mocker.patch.object(c, "broadcast_state", AsyncMock())
    await c.connect()

    saved = patched_state["codemanga_room_ABC"]
    assert set(saved["players"]) == {"cid-host"}  # no duplicate
    assert saved["players"]["cid-host"]["role"] == "spymaster"  # preserved
    assert saved["players"]["cid-host"]["channel"] == "new-chan"  # channel updated
    assert saved["host"] == "cid-host"


# --------------------------------------------------------------------------- #
# receive routing
# --------------------------------------------------------------------------- #
async def test_receive_bails_when_not_a_member(patched_state, mocker):
    patched_state["codemanga_room_ABC"] = _fresh_room()
    c = _make_consumer(cid="stranger")
    save = mocker.patch.object(c, "save_room", AsyncMock())
    await c.receive(json.dumps({"action": "chat", "message": "hi"}))
    save.assert_not_awaited()


async def test_set_player_updates_team_and_role(patched_state, mocker):
    room = _fresh_room()
    room["players"]["cid-host"] = _blue_operative()
    patched_state["codemanga_room_ABC"] = room
    c = _make_consumer(cid="cid-host")
    mocker.patch.object(c, "broadcast_state", AsyncMock())

    await c.receive(
        json.dumps(
            {
                "action": "set_player",
                "name": "Naruto",
                "team": "red",
                "role": "spymaster",
            }
        )
    )
    me = patched_state["codemanga_room_ABC"]["players"]["cid-host"]
    assert me["name"] == "Naruto" and me["team"] == "red" and me["role"] == "spymaster"


async def test_set_categories_keeps_only_known(patched_state, mocker):
    room = _fresh_room(host="cid-host")
    room["players"]["cid-host"] = {
        "name": "h",
        "team": "blue",
        "role": "spymaster",
        "channel": "chan-host",
    }
    patched_state["codemanga_room_ABC"] = room
    c = _make_consumer(cid="cid-host")
    mocker.patch.object(c, "broadcast_state", AsyncMock())

    await c.receive(
        json.dumps(
            {"action": "set_categories", "categories": ["Anime", "Game", "BOGUS"]}
        )
    )
    assert patched_state["codemanga_room_ABC"]["categories"] == ["Anime", "Game"]


async def test_collect_cards_merges_categories_and_dedupes(patched_catalog):
    """_collect_cards unions catalogs by (title, image), skipping imageless items."""
    c = _make_consumer()
    cards = c._collect_cards(["Anime"])
    assert len(cards) == 40  # fake catalog has 40 titled+imaged items
    assert all("title" in x and "image" in x for x in cards)


async def test_start_game_builds_grid_no_redirect(
    patched_state, patched_catalog, mocker
):
    room = _fresh_room()
    room["players"]["cid-host"] = {
        "name": "h",
        "team": "blue",
        "role": "spymaster",
        "channel": "chan-host",
    }
    patched_state["codemanga_room_ABC"] = room
    c = _make_consumer(cid="cid-host")
    mocker.patch.object(c, "broadcast_state", AsyncMock())

    await c.receive(json.dumps({"action": "start_game"}))

    saved = patched_state["codemanga_room_ABC"]
    assert saved["state"] == "playing"
    assert len(saved["grid"]) == 25
    # No redirect group_send is emitted (single-page room).
    c.channel_layer.group_send.assert_not_awaited()


async def test_start_game_ignored_for_non_host(patched_state, patched_catalog, mocker):
    room = _fresh_room(host="cid-host")
    room["players"]["cid-host"] = {**_blue_operative(), "channel": "chan-host"}
    room["players"]["cid-guest"] = {
        "name": "g",
        "team": "red",
        "role": "spymaster",
        "channel": "chan-guest",
    }
    patched_state["codemanga_room_ABC"] = room
    c = _make_consumer(cid="cid-guest", channel_name="chan-guest")
    mocker.patch.object(c, "broadcast_state", AsyncMock())

    await c.receive(json.dumps({"action": "start_game"}))
    assert patched_state["codemanga_room_ABC"]["state"] == "lobby"


async def test_chat_appends_message(patched_state, mocker):
    room = _fresh_room()
    room["players"]["cid-host"] = _blue_operative()
    patched_state["codemanga_room_ABC"] = room
    c = _make_consumer(cid="cid-host")
    mocker.patch.object(c, "broadcast_state", AsyncMock())

    await c.receive(json.dumps({"action": "chat", "message": "gg"}))
    msgs = patched_state["codemanga_room_ABC"]["messages"]
    assert msgs[-1] == {"user": "Op", "text": "gg"}


async def test_back_to_lobby_resets_but_keeps_players(patched_state, mocker):
    room = _playing_room_with_grid()
    room["host"] = "cid-host"
    room["players"]["cid-host"] = {
        "name": "h",
        "team": "blue",
        "role": "spymaster",
        "channel": "chan-host",
    }
    room["winner"] = "blue"
    patched_state["codemanga_room_ABC"] = room
    c = _make_consumer(cid="cid-host")
    mocker.patch.object(c, "broadcast_state", AsyncMock())

    await c.receive(json.dumps({"action": "back_to_lobby"}))
    saved = patched_state["codemanga_room_ABC"]
    assert saved["state"] == "lobby" and saved["grid"] == [] and saved["winner"] is None
    assert set(saved["players"]) == {"cid-op", "cid-host"}  # players kept


# --------------------------------------------------------------------------- #
# generate_grid
# --------------------------------------------------------------------------- #
async def test_generate_grid_shape_and_roles(patched_catalog):
    c = _make_consumer()
    room = _fresh_room()
    await c.generate_grid(room)
    roles = [card["role"] for card in room["grid"]]
    assert len(room["grid"]) == 25
    assert roles.count("blue") == 9
    assert roles.count("red") == 8
    assert roles.count("neutral") == 7
    assert roles.count("assassin") == 1
    assert all(card["revealed"] is False for card in room["grid"])


async def test_generate_grid_noop_when_catalog_too_small(mocker):
    catalog = MagicMock()
    catalog.load_data = MagicMock(return_value={"db": [{"title": "x"}]})
    container = MagicMock()
    container.catalog_service = catalog
    mocker.patch.object(cm, "get_container", return_value=container)
    c = _make_consumer()
    room = _fresh_room()
    await c.generate_grid(room)
    assert room["grid"] == []


# --------------------------------------------------------------------------- #
# clue gating
# --------------------------------------------------------------------------- #
async def test_clue_set_by_current_team_spymaster():
    c = _make_consumer()
    room = _playing_room_with_grid()
    room["clue"] = None
    spy = {"name": "S", "team": "blue", "role": "spymaster", "channel": "c"}
    c.handle_clue(room, spy, {"word": "sword", "number": 3})
    assert room["clue"] == {
        "team": "blue",
        "word": "sword",
        "number": 3,
        "guesses_left": 4,
    }


async def test_clue_rejected_from_wrong_team_or_operative():
    c = _make_consumer()
    room = _playing_room_with_grid()
    room["clue"] = None
    red_spy = {"name": "R", "team": "red", "role": "spymaster", "channel": "c"}
    c.handle_clue(room, red_spy, {"word": "x", "number": 1})
    assert room["clue"] is None  # not their turn
    blue_op = _blue_operative()
    c.handle_clue(room, blue_op, {"word": "x", "number": 1})
    assert room["clue"] is None  # operatives can't clue


# --------------------------------------------------------------------------- #
# click gating + rules
# --------------------------------------------------------------------------- #
async def test_click_requires_active_clue():
    c = _make_consumer()
    room = _playing_room_with_grid()
    room["clue"] = None
    c.handle_card_click(room, _blue_operative(), 0)
    assert room["grid"][0]["revealed"] is False


async def test_click_rejected_for_wrong_team_operative():
    c = _make_consumer()
    room = _playing_room_with_grid()
    red_op = {"name": "R", "team": "red", "role": "operative", "channel": "c"}
    c.handle_card_click(room, red_op, 0)
    assert room["grid"][0]["revealed"] is False


async def test_click_rejected_for_spymaster():
    c = _make_consumer()
    room = _playing_room_with_grid()
    spy = {"name": "S", "team": "blue", "role": "spymaster", "channel": "c"}
    c.handle_card_click(room, spy, 0)
    assert room["grid"][0]["revealed"] is False


async def test_correct_guess_keeps_turn_decrements_guesses():
    c = _make_consumer()
    room = _playing_room_with_grid()  # guesses_left 6
    c.handle_card_click(room, _blue_operative(), 0)  # blue card
    assert room["grid"][0]["revealed"] is True
    assert room["turn"] == "blue"
    assert room["blue_score"] == 1
    assert room["clue"]["guesses_left"] == 5


async def test_wrong_team_card_switches_turn_and_clears_clue():
    c = _make_consumer()
    room = _playing_room_with_grid()
    c.handle_card_click(room, _blue_operative(), 9)  # red card
    assert room["turn"] == "red"
    assert room["red_score"] == 1
    assert room["clue"] is None


async def test_neutral_card_ends_turn():
    c = _make_consumer()
    room = _playing_room_with_grid()
    c.handle_card_click(room, _blue_operative(), 17)  # neutral
    assert room["turn"] == "red"
    assert room["clue"] is None


async def test_exhausting_guesses_ends_turn():
    c = _make_consumer()
    room = _playing_room_with_grid()
    room["clue"]["guesses_left"] = 1  # last allowed guess
    c.handle_card_click(room, _blue_operative(), 0)  # correct blue
    assert room["grid"][0]["revealed"] is True
    assert room["turn"] == "red"  # ran out → turn ends
    assert room["clue"] is None


async def test_assassin_makes_opponent_win():
    c = _make_consumer()
    room = _playing_room_with_grid()
    c.handle_card_click(room, _blue_operative(), 24)
    assert room["winner"] == "red"
    assert room["clue"] is None


async def test_revealing_all_blue_wins():
    c = _make_consumer()
    room = _playing_room_with_grid()
    for i in range(8):
        room["grid"][i]["revealed"] = True
    c.handle_card_click(room, _blue_operative(), 8)  # 9th blue
    assert room["blue_score"] == 9
    assert room["winner"] == "blue"


async def test_click_ignored_when_not_playing_or_won():
    c = _make_consumer()
    lobby = _playing_room_with_grid()
    lobby["state"] = "lobby"
    c.handle_card_click(lobby, _blue_operative(), 0)
    assert lobby["grid"][0]["revealed"] is False

    won = _playing_room_with_grid()
    won["winner"] = "blue"
    c.handle_card_click(won, _blue_operative(), 1)
    assert won["grid"][1]["revealed"] is False


# --------------------------------------------------------------------------- #
# broadcast_state
# --------------------------------------------------------------------------- #
async def test_broadcast_masks_for_operative_reveals_for_spymaster(patched_state):
    room = _playing_room_with_grid()
    room["grid"][0]["revealed"] = True
    room["players"] = {
        "cid-spy": {
            "name": "Spy",
            "team": "blue",
            "role": "spymaster",
            "channel": "chan-spy",
        },
        "cid-op": {
            "name": "Op",
            "team": "red",
            "role": "operative",
            "channel": "chan-op",
        },
    }
    room["host"] = "cid-spy"
    patched_state["codemanga_room_ABC"] = room

    c = _make_consumer()
    await c.broadcast_state()
    by_channel = {
        call.args[0]: call.args[1] for call in c.channel_layer.send.call_args_list
    }
    assert set(by_channel) == {"chan-spy", "chan-op"}

    spy_grid = by_channel["chan-spy"]["message"]["room"]["grid"]
    op_grid = by_channel["chan-op"]["message"]["room"]["grid"]
    assert spy_grid[24]["role"] == "assassin"  # spymaster sees truth
    assert op_grid[0]["role"] == "blue"  # revealed → real
    assert op_grid[24]["role"] == "unknown"  # hidden → masked

    # Public player shape carries id + is_host.
    players = by_channel["chan-op"]["message"]["room"]["players"]
    assert {p["id"] for p in players} == {"cid-spy", "cid-op"}
    assert any(p["is_host"] for p in players)
    assert by_channel["chan-op"]["message"]["my_team"] == "red"


async def test_broadcast_noop_when_room_missing(patched_state):
    c = _make_consumer()
    await c.broadcast_state()
    c.channel_layer.send.assert_not_called()
