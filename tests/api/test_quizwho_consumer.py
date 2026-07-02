"""Real-behavior tests for the QuizWhoConsumer (real-time 'Qui est-ce ?' duel).

Unit-style: the consumer is driven directly with I/O boundaries mocked (Channels
layer, ``accept``), persistence patched (``state_adapter``) and the container
(catalog + Akinetix engine) faked. Players are keyed by a stable cid (?cid=).
Asserts game logic + protocol: player numbering, board/secret setup, turn-gated
ask/guess, attribute-based elimination, win + per-player secret masking.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from animetix.consumers import quizwho as qw

pytestmark = pytest.mark.asyncio


# --------------------------------------------------------------------------- #
# Fakes / fixtures
# --------------------------------------------------------------------------- #
class _Formatter:
    def format(self, at):
        return f"est {at}"


class _FakeEngine:
    formatter = _Formatter()

    def _item_attribute_set(self, item, fine):
        return set(item.get("attrs", []))

    def _check_attribute_instance(self, item, attr, fine):
        return attr in item.get("attrs", [])


def _fake_db(n=16):
    # Half have "fille", evens have "magie" → discriminating attributes exist.
    db = []
    for i in range(n):
        attrs = []
        if i < n // 2:
            attrs.append("fille")
        if i % 2 == 0:
            attrs.append("magie")
        db.append(
            {"id": str(i), "title": f"C{i}", "image": f"i{i}.png", "attrs": attrs}
        )
    return db


@pytest.fixture
def patched(mocker):
    """Patch state_adapter (in-memory) + get_container (fake catalog/engine)."""
    store = {}

    async def _get(k):
        return store.get(k)

    async def _set(k, v, timeout=None):
        store[k] = v

    async def _del(k):
        store.pop(k, None)

    mocker.patch.object(qw.state_adapter, "get_state", side_effect=_get)
    mocker.patch.object(qw.state_adapter, "set_state", side_effect=_set)
    mocker.patch.object(qw.state_adapter, "delete_state", side_effect=_del)

    db = _fake_db()
    catalog = {
        "db": db,
        "id_to_full_data": {it["id"]: it for it in db},
    }
    cs = MagicMock()
    cs.load_data = MagicMock(return_value=catalog)
    cs.get_akinetix_attributes = MagicMock(return_value={})
    ak = MagicMock()
    ak.engine = _FakeEngine()
    container = MagicMock()
    container.core.catalog_service = MagicMock(return_value=cs)
    container.core.akinetix_service = MagicMock(return_value=ak)
    mocker.patch.object(qw, "get_container", return_value=container)
    return store


def _make(cid="p1", channel="chan1", room_code="abc"):
    c = qw.QuizWhoConsumer()
    c.room_code = room_code.upper()
    c.room_group_name = f"quizwho_{room_code.upper()}"
    c.cid = cid
    c.channel_name = channel
    c.scope = {
        "url_route": {"kwargs": {"room_code": room_code}},
        "query_string": f"cid={cid}".encode(),
    }
    c.accept = AsyncMock()
    c.channel_layer = AsyncMock()
    return c


async def _connect(cid, channel, store):
    c = _make(cid=cid, channel=channel)
    await c.connect()
    return c


def _room(store):
    return store["quizwho_room_ABC"]


# --------------------------------------------------------------------------- #
# Connection / numbering
# --------------------------------------------------------------------------- #
async def test_first_two_players_get_num_1_and_2(patched):
    await _connect("p1", "c1", patched)
    await _connect("p2", "c2", patched)
    room = _room(patched)
    assert room["players"]["p1"]["num"] == 1
    assert room["players"]["p2"]["num"] == 2
    assert room["host"] == "p1"


async def test_third_player_is_spectator(patched):
    await _connect("p1", "c1", patched)
    await _connect("p2", "c2", patched)
    await _connect("p3", "c3", patched)
    assert _room(patched)["players"]["p3"]["num"] == 0


# --------------------------------------------------------------------------- #
# Settings + start
# --------------------------------------------------------------------------- #
async def test_start_requires_two_players(patched):
    c = await _connect("p1", "c1", patched)
    await c.receive(json.dumps({"action": "start_game"}))
    assert _room(patched)["state"] == "lobby"  # only one player


async def test_start_builds_board_secrets_and_turn(patched):
    await _connect("p1", "c1", patched)
    c2 = await _connect("p2", "c2", patched)
    # host (p1) starts
    host = _make(cid="p1", channel="c1")
    await host.receive(json.dumps({"action": "start_game"}))
    room = _room(patched)
    assert room["state"] == "playing"
    assert len(room["board"]) == 16
    assert room["questions"]
    assert room["secrets"]["1"] and room["secrets"]["2"]
    assert room["secrets"]["1"] != room["secrets"]["2"]
    assert room["turn"] == 1
    _ = c2  # silence unused


async def test_set_settings_validates(patched):
    c = await _connect("p1", "c1", patched)
    await c.receive(
        json.dumps(
            {"action": "set_settings", "media_type": "Manga", "difficulty": "Hard"}
        )
    )
    room = _room(patched)
    assert room["media_type"] == "Manga" and room["difficulty"] == "Hard"
    await c.receive(json.dumps({"action": "set_settings", "media_type": "BOGUS"}))
    assert _room(patched)["media_type"] == "Manga"  # unchanged


# --------------------------------------------------------------------------- #
# Playing: ask / guess
# --------------------------------------------------------------------------- #
async def _start_game(patched):
    await _connect("p1", "c1", patched)
    await _connect("p2", "c2", patched)
    host = _make(cid="p1", channel="c1")
    await host.receive(json.dumps({"action": "start_game"}))
    return _room(patched)


async def test_ask_eliminates_and_flips_turn(patched):
    room = await _start_game(patched)
    # Make p2's secret a known item so the answer is deterministic.
    room["secrets"]["2"] = "0"  # item 0 has attrs [fille, magie]
    patched["quizwho_room_ABC"] = room
    attr = "fille"
    p1 = _make(cid="p1", channel="c1")
    await p1.receive(json.dumps({"action": "ask", "attribute": attr}))
    room = _room(patched)
    # Answer OUI (item 0 is 'fille'); non-'fille' portraits eliminated on p1 side.
    assert room["last_answer"]["answer"] == "OUI"
    assert room["last_answer"]["by"] == 1
    assert len(room["eliminated"]["1"]) > 0
    assert room["turn"] == 2  # flipped


async def test_ask_rejected_when_not_your_turn(patched):
    await _start_game(patched)
    p2 = _make(cid="p2", channel="c2")  # p2, but it's p1's turn
    await p2.receive(json.dumps({"action": "ask", "attribute": "fille"}))
    assert _room(patched)["last_answer"] is None


async def test_ask_rejects_unknown_attribute(patched):
    await _start_game(patched)
    p1 = _make(cid="p1", channel="c1")
    await p1.receive(json.dumps({"action": "ask", "attribute": "not_a_real_attr"}))
    assert _room(patched)["last_answer"] is None


async def test_guess_correct_wins(patched):
    room = await _start_game(patched)
    room["secrets"]["2"] = "7"
    patched["quizwho_room_ABC"] = room
    p1 = _make(cid="p1", channel="c1")
    await p1.receive(json.dumps({"action": "guess", "guess_id": "7"}))
    room = _room(patched)
    assert room["winner"] == 1 and room["state"] == "ended"


async def test_guess_wrong_eliminates_and_flips(patched):
    room = await _start_game(patched)
    room["secrets"]["2"] = "7"
    patched["quizwho_room_ABC"] = room
    p1 = _make(cid="p1", channel="c1")
    await p1.receive(json.dumps({"action": "guess", "guess_id": "3"}))
    room = _room(patched)
    assert room["winner"] is None
    assert "3" in room["eliminated"]["1"]
    assert room["turn"] == 2


# --------------------------------------------------------------------------- #
# Custom questions (opponent-answered) + manual cross-off
# --------------------------------------------------------------------------- #
async def test_custom_question_pends_then_opponent_answers(patched):
    await _start_game(patched)
    p1 = _make(cid="p1", channel="c1")
    await p1.receive(
        json.dumps({"action": "ask_custom", "text": "a les cheveux bleus ?"})
    )
    room = _room(patched)
    assert room["pending"] == {
        "by": 1,
        "name": room["players"]["p1"]["name"],
        "text": "a les cheveux bleus ?",
    }
    # p1 (asker) can't answer their own question.
    await p1.receive(json.dumps({"action": "answer_custom", "answer": "OUI"}))
    assert _room(patched)["pending"] is not None
    # p2 (opponent) answers → recorded, pending cleared, asker's turn ends.
    p2 = _make(cid="p2", channel="c2")
    await p2.receive(json.dumps({"action": "answer_custom", "answer": "OUI"}))
    room = _room(patched)
    assert room["pending"] is None
    assert room["last_answer"] == {
        "by": 1,
        "name": room["players"]["p1"]["name"],
        "label": "a les cheveux bleus ?",
        "answer": "OUI",
    }
    assert room["turn"] == 2


async def test_ask_blocked_while_pending(patched):
    await _start_game(patched)
    p1 = _make(cid="p1", channel="c1")
    await p1.receive(json.dumps({"action": "ask_custom", "text": "q ?"}))
    await p1.receive(json.dumps({"action": "ask", "attribute": "fille"}))
    # last_answer stays None: the preset ask is blocked while a custom Q pends.
    assert _room(patched)["last_answer"] is None


async def test_toggle_card_crosses_off_and_back(patched):
    await _start_game(patched)
    p2 = _make(cid="p2", channel="c2")  # note-taking allowed even off-turn
    await p2.receive(json.dumps({"action": "toggle_card", "card_id": "5"}))
    assert "5" in _room(patched)["eliminated"]["2"]
    await p2.receive(json.dumps({"action": "toggle_card", "card_id": "5"}))
    assert "5" not in _room(patched)["eliminated"]["2"]


# --------------------------------------------------------------------------- #
# Broadcast masking
# --------------------------------------------------------------------------- #
async def test_broadcast_gives_each_player_only_their_secret(patched):
    room = await _start_game(patched)
    c = _make(cid="p1", channel="c1")
    await c.broadcast_state()
    sends = {call.args[0]: call.args[1] for call in c.channel_layer.send.call_args_list}
    assert set(sends) == {"c1", "c2"}
    p1_msg = sends["c1"]["message"]
    p2_msg = sends["c2"]["message"]
    assert p1_msg["your_num"] == 1
    assert p1_msg["your_secret_id"] == room["secrets"]["1"]
    assert p2_msg["your_secret_id"] == room["secrets"]["2"]
    # The opponent's secret is never sent to you.
    assert p1_msg["your_secret_id"] != room["secrets"]["2"]
