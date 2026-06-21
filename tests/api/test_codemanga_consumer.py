"""Real-behavior tests for the CodeMangaConsumer (Codenames-style game).

These are unit-style tests: we instantiate the consumer directly and drive its
async methods, mocking only the I/O boundaries (Channels layer, ``self.send`` /
``self.accept``) and the persistence layer (``state_adapter`` + the catalog
``get_container``). No real DB / Redis / network / Channels routing is used.

What is asserted is the *game logic and protocol*, not bare mock calls:
  * grid generation shape (25 cards) and exact role distribution (9/8/7/1),
  * card-click reveal rules, turn switching, assassin loss, score-based wins,
  * the redirect / state payloads that are broadcast,
  * spymaster vs operative grid visibility,
  * action routing in ``receive`` and lobby bootstrap in ``connect``.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from animetix.consumers import codemanga as cm

pytestmark = pytest.mark.asyncio


# --------------------------------------------------------------------------- #
# Helpers / fixtures
# --------------------------------------------------------------------------- #
def _make_consumer(room_code="abc", channel_name="chan-host"):
    """Build a consumer with all async I/O boundaries mocked."""
    c = cm.CodeMangaConsumer()
    c.room_code = room_code.upper()
    c.room_group_name = f"codemanga_{room_code.upper()}"
    c.channel_name = channel_name
    c.scope = {"url_route": {"kwargs": {"room_code": room_code}}}
    c.send = AsyncMock()
    c.accept = AsyncMock()
    c.close = AsyncMock()
    c.channel_layer = AsyncMock()
    return c


def _fresh_room(host="chan-host"):
    return {
        "host": host,
        "players": {},
        "state": "lobby",
        "grid": [],
        "turn": "blue",
        "blue_score": 0,
        "red_score": 0,
        "winner": None,
    }


def _playing_room_with_grid(host="chan-host"):
    """A room mid-game with a fully-controlled 25-card grid.

    Roles laid out deterministically so tests can target a known index:
      0-8   -> blue   (9)
      9-16  -> red    (8)
      17-23 -> neutral(7)
      24    -> assassin(1)
    """
    grid = []
    for i in range(25):
        if i < 9:
            role = "blue"
        elif i < 17:
            role = "red"
        elif i < 24:
            role = "neutral"
        else:
            role = "assassin"
        grid.append(
            {"title": f"T{i}", "image": f"i{i}.png", "role": role, "revealed": False}
        )
    room = _fresh_room(host)
    room.update(
        {
            "state": "playing",
            "grid": grid,
            "turn": "blue",
            "blue_score": 0,
            "red_score": 0,
            "winner": None,
        }
    )
    return room


@pytest.fixture
def patched_state(mocker):
    """Patch the module-level state_adapter so get_room/save_room hit an in-memory store.

    Returns the dict store keyed by the full cache key the consumer uses.
    """
    store = {}

    async def _get(key):
        return store.get(key)

    async def _set(key, value, timeout=None):
        store[key] = value

    mocker.patch.object(cm.state_adapter, "get_state", side_effect=_get)
    mocker.patch.object(cm.state_adapter, "set_state", side_effect=_set)
    return store


@pytest.fixture
def patched_catalog(mocker):
    """Patch get_container().catalog_service.load_data to return a fake anime DB."""
    db = [{"title": f"Anime {i}", "image": f"img{i}.png"} for i in range(40)]
    catalog = MagicMock()
    catalog.load_data = MagicMock(return_value={"db": db})
    container = MagicMock()
    container.catalog_service = catalog
    mocker.patch.object(cm, "get_container", return_value=container)
    return catalog


# --------------------------------------------------------------------------- #
# get_room / save_room round-trip
# --------------------------------------------------------------------------- #
async def test_save_then_get_room_roundtrips_under_namespaced_key(patched_state):
    """save_room stores under codemanga_room_<CODE>; get_room reads it back."""
    c = _make_consumer(room_code="xyz")
    room = _fresh_room()
    await c.save_room(room)
    assert "codemanga_room_XYZ" in patched_state
    assert await c.get_room() == room


# --------------------------------------------------------------------------- #
# connect
# --------------------------------------------------------------------------- #
async def test_connect_bootstraps_lobby_and_registers_player(patched_state, mocker):
    """First connect creates a lobby room, joins the group, accepts, broadcasts."""
    c = cm.CodeMangaConsumer()
    c.channel_name = "chan-host"
    c.scope = {"url_route": {"kwargs": {"room_code": "abc"}}}
    c.send = AsyncMock()
    c.accept = AsyncMock()
    c.channel_layer = AsyncMock()
    mocker.patch.object(c, "broadcast_state", AsyncMock())

    await c.connect()

    # room_code uppercased, group name derived from it
    assert c.room_code == "ABC"
    assert c.room_group_name == "codemanga_ABC"
    # group membership + accept happened
    c.channel_layer.group_add.assert_awaited_once_with("codemanga_ABC", "chan-host")
    c.accept.assert_awaited_once()
    c.broadcast_state.assert_awaited_once()
    # room persisted as a fresh lobby with this channel as host + a registered player
    room = patched_state["codemanga_room_ABC"]
    assert room["state"] == "lobby"
    assert room["host"] == "chan-host"
    assert "chan-host" in room["players"]
    player = room["players"]["chan-host"]
    assert player["team"] is None and player["role"] is None
    assert player["name"].startswith("Fan #")


async def test_connect_preserves_existing_room_and_adds_second_player(
    patched_state, mocker
):
    """A second connect to an existing room keeps host/state and adds the player."""
    patched_state["codemanga_room_ABC"] = _fresh_room(host="chan-host")
    patched_state["codemanga_room_ABC"]["players"]["chan-host"] = {
        "name": "Fan #111",
        "team": "blue",
        "role": "spymaster",
    }

    c = _make_consumer(room_code="abc", channel_name="chan-guest")
    mocker.patch.object(c, "broadcast_state", AsyncMock())
    await c.connect()

    room = patched_state["codemanga_room_ABC"]
    assert room["host"] == "chan-host"  # original host untouched
    assert set(room["players"]) == {"chan-host", "chan-guest"}
    assert room["players"]["chan-host"]["role"] == "spymaster"  # preserved


# --------------------------------------------------------------------------- #
# receive routing
# --------------------------------------------------------------------------- #
async def test_receive_returns_early_when_no_room(patched_state, mocker):
    """No room in store -> receive bails before touching save/broadcast."""
    c = _make_consumer()
    save = mocker.patch.object(c, "save_room", AsyncMock())
    bcast = mocker.patch.object(c, "broadcast_state", AsyncMock())
    await c.receive(json.dumps({"action": "set_player"}))
    save.assert_not_awaited()
    bcast.assert_not_awaited()


async def test_receive_set_player_updates_player_and_broadcasts(patched_state, mocker):
    """set_player mutates the calling player's name/team/role, then persists + broadcasts."""
    room = _fresh_room()
    room["players"]["chan-host"] = {"name": "old", "team": None, "role": None}
    patched_state["codemanga_room_ABC"] = room

    c = _make_consumer()
    bcast = mocker.patch.object(c, "broadcast_state", AsyncMock())
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

    updated = patched_state["codemanga_room_ABC"]["players"]["chan-host"]
    assert updated == {"name": "Naruto", "team": "red", "role": "spymaster"}
    bcast.assert_awaited_once()


async def test_receive_start_game_sets_playing_and_sends_redirect(
    patched_state, patched_catalog, mocker
):
    """start_game generates the grid, flips state to playing, and group-sends a redirect."""
    room = _fresh_room()
    room["players"]["chan-host"] = {"name": "h", "team": "blue", "role": "spymaster"}
    patched_state["codemanga_room_ABC"] = room

    c = _make_consumer()
    mocker.patch.object(c, "broadcast_state", AsyncMock())
    await c.receive(json.dumps({"action": "start_game"}))

    saved = patched_state["codemanga_room_ABC"]
    assert saved["state"] == "playing"
    assert len(saved["grid"]) == 25

    # the redirect was group_sent to the game URL
    args, _ = c.channel_layer.group_send.call_args
    assert args[0] == "codemanga_ABC"
    payload = args[1]
    assert payload["type"] == "send_msg"
    assert payload["message"] == {
        "type": "redirect",
        "url": "/codemanga/game/ABC/",
    }


async def test_receive_click_card_routes_to_handler(patched_state, mocker):
    """click_card delegates to handle_card_click with the provided index."""
    room = _playing_room_with_grid()
    room["players"]["chan-host"] = {"name": "h", "team": "blue", "role": "operative"}
    patched_state["codemanga_room_ABC"] = room

    c = _make_consumer()
    handler = mocker.patch.object(c, "handle_card_click", AsyncMock())
    mocker.patch.object(c, "broadcast_state", AsyncMock())
    await c.receive(json.dumps({"action": "click_card", "index": 4}))

    handler.assert_awaited_once()
    called_room, called_idx = handler.call_args.args
    assert called_idx == 4
    assert called_room["state"] == "playing"


# --------------------------------------------------------------------------- #
# generate_grid
# --------------------------------------------------------------------------- #
async def test_generate_grid_shape_and_role_distribution(patched_catalog):
    """25 unique cards, exact role counts, all hidden, scores/turn/winner reset."""
    c = _make_consumer()
    room = _fresh_room()
    room["blue_score"], room["red_score"], room["turn"], room["winner"] = (
        5,
        4,
        "red",
        "blue",
    )

    await c.generate_grid(room)

    grid = room["grid"]
    assert len(grid) == 25
    roles = [card["role"] for card in grid]
    assert roles.count("blue") == 9
    assert roles.count("red") == 8
    assert roles.count("neutral") == 7
    assert roles.count("assassin") == 1
    assert all(card["revealed"] is False for card in grid)
    # cards carry title + image from the catalog
    assert all("title" in card and "image" in card for card in grid)
    # counters reset by generation
    assert room["blue_score"] == 0
    assert room["red_score"] == 0
    assert room["turn"] == "blue"
    assert room["winner"] is None


async def test_generate_grid_noop_when_catalog_empty(mocker):
    """No catalog data -> grid is left untouched (early return)."""
    catalog = MagicMock()
    catalog.load_data = MagicMock(return_value=None)
    container = MagicMock()
    container.catalog_service = catalog
    mocker.patch.object(cm, "get_container", return_value=container)

    c = _make_consumer()
    room = _fresh_room()
    await c.generate_grid(room)
    assert room["grid"] == []


# --------------------------------------------------------------------------- #
# handle_card_click
# --------------------------------------------------------------------------- #
async def test_click_correct_card_keeps_turn_and_scores(patched_state):
    """Blue's turn revealing a blue card: stays blue's turn, blue_score increments."""
    c = _make_consumer()
    room = _playing_room_with_grid()
    await c.handle_card_click(room, 0)  # index 0 is blue

    assert room["grid"][0]["revealed"] is True
    assert room["turn"] == "blue"  # correct guess -> no switch
    assert room["blue_score"] == 1
    assert room["red_score"] == 0
    assert room["winner"] is None


async def test_click_wrong_team_card_switches_turn(patched_state):
    """Blue's turn revealing a red card: turn flips to red, red_score increments."""
    c = _make_consumer()
    room = _playing_room_with_grid()
    await c.handle_card_click(room, 9)  # index 9 is red

    assert room["grid"][9]["revealed"] is True
    assert room["turn"] == "red"  # wrong team -> switch
    assert room["red_score"] == 1
    assert room["blue_score"] == 0


async def test_click_neutral_card_switches_turn_without_score(patched_state):
    """A neutral reveal ends the turn but scores nothing for either side."""
    c = _make_consumer()
    room = _playing_room_with_grid()
    await c.handle_card_click(room, 17)  # neutral

    assert room["grid"][17]["revealed"] is True
    assert room["turn"] == "red"
    assert room["blue_score"] == 0
    assert room["red_score"] == 0


async def test_click_assassin_makes_opponent_win(patched_state):
    """Blue hits the assassin -> red wins immediately."""
    c = _make_consumer()
    room = _playing_room_with_grid()
    await c.handle_card_click(room, 24)  # assassin

    assert room["winner"] == "red"


async def test_click_already_revealed_is_noop(patched_state):
    """Clicking an already-revealed card changes nothing."""
    c = _make_consumer()
    room = _playing_room_with_grid()
    room["grid"][0]["revealed"] = True
    room["blue_score"] = 1
    await c.handle_card_click(room, 0)

    # turn unchanged, score not recomputed off this no-op click
    assert room["turn"] == "blue"
    assert room["winner"] is None


async def test_click_ignored_when_not_playing_or_already_won(patched_state):
    """Guards: lobby state and a decided game both block reveals."""
    c = _make_consumer()

    lobby = _playing_room_with_grid()
    lobby["state"] = "lobby"
    await c.handle_card_click(lobby, 0)
    assert lobby["grid"][0]["revealed"] is False

    won = _playing_room_with_grid()
    won["winner"] = "blue"
    await c.handle_card_click(won, 9)
    assert won["grid"][9]["revealed"] is False


async def test_revealing_all_blue_cards_wins_for_blue(patched_state):
    """Reaching 9 revealed blue cards declares blue the winner."""
    c = _make_consumer()
    room = _playing_room_with_grid()
    # Pre-reveal 8 blue cards; the 9th click should trigger the win.
    for i in range(8):
        room["grid"][i]["revealed"] = True
    await c.handle_card_click(room, 8)  # 9th blue

    assert room["blue_score"] == 9
    assert room["winner"] == "blue"


async def test_revealing_all_red_cards_wins_for_red(patched_state):
    """Reaching 8 revealed red cards declares red the winner."""
    c = _make_consumer()
    room = _playing_room_with_grid()
    room["turn"] = "red"
    for i in range(9, 16):  # 7 red revealed
        room["grid"][i]["revealed"] = True
    await c.handle_card_click(room, 16)  # 8th red

    assert room["red_score"] == 8
    assert room["winner"] == "red"


# --------------------------------------------------------------------------- #
# broadcast_state
# --------------------------------------------------------------------------- #
async def test_broadcast_masks_roles_for_operative_but_reveals_for_spymaster(
    patched_state,
):
    """Spymaster receives the full grid with true roles; operatives get masked roles."""
    room = _playing_room_with_grid()
    room["players"] = {
        "chan-spy": {"name": "Spy", "team": "blue", "role": "spymaster"},
        "chan-op": {"name": "Op", "team": "red", "role": "operative"},
    }
    # Reveal one card so we can observe masking on the hidden ones.
    room["grid"][0]["revealed"] = True
    patched_state["codemanga_room_ABC"] = room

    c = _make_consumer()
    await c.broadcast_state()

    # Two per-channel sends, one per player.
    sends = c.channel_layer.send.call_args_list
    by_channel = {call.args[0]: call.args[1] for call in sends}
    assert set(by_channel) == {"chan-spy", "chan-op"}

    spy_grid = by_channel["chan-spy"]["message"]["room"]["grid"]
    op_grid = by_channel["chan-op"]["message"]["room"]["grid"]

    # Spymaster sees the real (full) grid objects: hidden assassin role is truthful.
    assert spy_grid[24]["role"] == "assassin"
    # Operative sees hidden roles masked to "unknown" but revealed ones truthful.
    assert op_grid[0]["role"] == "blue"  # revealed -> real
    assert op_grid[24]["role"] == "unknown"  # hidden -> masked

    # Per-player identity fields are echoed back correctly.
    assert by_channel["chan-spy"]["message"]["my_role"] == "spymaster"
    assert by_channel["chan-op"]["message"]["my_team"] == "red"


async def test_broadcast_noop_when_room_missing(patched_state):
    """No room -> broadcast sends nothing."""
    c = _make_consumer()
    await c.broadcast_state()
    c.channel_layer.send.assert_not_called()
