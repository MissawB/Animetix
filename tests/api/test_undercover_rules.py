"""Game-rule tests for the Undercover consumer (was ~38% covered).

The WebSocket plumbing (connect / set_name / chat) is already covered by
tests/backend/test_consumers.py through a real WebsocketCommunicator. What was
untested is the part that decides who wins: the voting/elimination loop, the
Mr. White guess, and the win conditions.

Those live on the consumer but are pure functions of the ``room`` dict, so we
drive them directly with the transport stubbed (``save_room`` /
``broadcast_state``). No channel layer, no cache, no WebSocket — the rules are
the subject, not the plumbing.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from animetix.consumers import undercover as uc
from animetix.consumers.undercover import (
    UndercoverConsumer,
    _guess_matches,
    _max_threats,
)


def _consumer(cid="p1"):
    c = UndercoverConsumer()
    c.room_code = "ABC"
    c.room_group_name = "undercover_ABC"
    c.cid = cid
    c.save_room = AsyncMock()
    c.broadcast_state = AsyncMock()
    c.channel_layer = MagicMock()
    return c


def _room(players, state="playing", **extra):
    room = UndercoverConsumer._fresh_room(None)
    room["state"] = state
    room["players"] = players
    room["civil_word"] = "Naruto"
    room["undercover_word"] = "Sasuke"
    room.update(extra)
    return room


def _p(name, role="Civil", alive=True):
    return {
        "name": name,
        "role": role,
        "word": "w",
        "image": None,
        "alive": alive,
        "channel": f"ch-{name}",
    }


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "n_players,expected",
    [(3, 1), (4, 1), (5, 2), (6, 2), (7, 3), (1, 1)],
)
def test_max_threats_keeps_civils_in_strict_majority(n_players, expected):
    # Threats must never open at parity: with n players, at most (n-1)//2.
    assert _max_threats(n_players) == expected


@pytest.mark.parametrize(
    "guess",
    ["Naruto", "naruto", "NARUTO", "  Naruto  ", "Narutoo", "Nartuo"],
)
def test_mrwhite_guess_tolerates_case_spacing_and_typos(guess):
    assert _guess_matches(guess, "Naruto") is True


def test_mrwhite_guess_tolerates_accents_and_missing_subtitle():
    assert _guess_matches("attaque des titans", "L'Attaque des Titans: Final") is True


def test_mrwhite_guess_rejects_a_different_title():
    assert _guess_matches("One Piece", "Naruto") is False


def test_mrwhite_guess_rejects_empty():
    assert _guess_matches("", "Naruto") is False
    assert _guess_matches("Naruto", "") is False


@pytest.mark.parametrize(
    "value,expected",
    [("3", 3), (3, 3), (99, 12), (-5, 1), (None, 7), ("abc", 7)],
)
def test_as_int_clamps_and_falls_back(value, expected):
    # default=7, lo=1, hi=12
    assert UndercoverConsumer._as_int(value, 7, 1, 12) == expected


# --------------------------------------------------------------------------- #
# Win conditions
# --------------------------------------------------------------------------- #
def test_civils_win_when_every_threat_is_out():
    c = _consumer()
    room = _room(
        {
            "p1": _p("A", "Civil"),
            "p2": _p("B", "Civil"),
            "p3": _p("C", "Undercover", alive=False),
        }
    )

    assert c._check_win(room) is True
    assert room["state"] == "ended"
    assert room["result"]["winner"] == "civils"
    assert room["result"]["reason"] == "all_threats_out"


def test_threats_win_on_parity_and_name_surviving_mrwhites():
    c = _consumer()
    room = _room(
        {
            "p1": _p("A", "Civil"),
            "p2": _p("B", "Undercover"),
            "p3": _p("C", "MrWhite"),
            "p4": _p("D", "Civil", alive=False),
        }
    )

    assert c._check_win(room) is True
    assert room["result"]["winner"] == "infiltres"
    assert room["result"]["reason"] == "parity"
    assert room["result"]["mrwhite_winners"] == ["C"]


def test_game_continues_while_civils_outnumber_threats():
    c = _consumer()
    room = _room(
        {
            "p1": _p("A", "Civil"),
            "p2": _p("B", "Civil"),
            "p3": _p("C", "Undercover"),
        }
    )

    assert c._check_win(room) is False
    assert room["state"] == "playing"
    assert room["result"] is None


# --------------------------------------------------------------------------- #
# Voting / elimination loop
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_vote_is_ignored_outside_playing_state():
    c = _consumer()
    room = _room({"p1": _p("A"), "p2": _p("B")}, state="lobby")

    await c.handle_vote(room, "p2")

    assert room["votes"] == {}
    c.save_room.assert_not_called()


@pytest.mark.asyncio
async def test_self_vote_is_ignored():
    c = _consumer(cid="p1")
    room = _room({"p1": _p("A"), "p2": _p("B")})

    await c.handle_vote(room, "p1")

    assert room["votes"] == {}


@pytest.mark.asyncio
async def test_dead_players_cannot_vote_and_cannot_be_voted():
    c = _consumer(cid="p1")
    dead_voter_room = _room({"p1": _p("A", alive=False), "p2": _p("B")})
    await c.handle_vote(dead_voter_room, "p2")
    assert dead_voter_room["votes"] == {}

    c2 = _consumer(cid="p1")
    dead_target_room = _room({"p1": _p("A"), "p2": _p("B", alive=False)})
    await c2.handle_vote(dead_target_room, "p2")
    assert dead_target_room["votes"] == {}


@pytest.mark.asyncio
async def test_partial_vote_waits_for_the_remaining_players():
    c = _consumer(cid="p1")
    room = _room({"p1": _p("A"), "p2": _p("B"), "p3": _p("C")})

    await c.handle_vote(room, "p2")

    # Not everyone has voted: the vote is recorded, nobody is eliminated yet.
    assert room["votes"] == {"p1": "p2"}
    assert room["players"]["p2"]["alive"] is True
    c.broadcast_state.assert_awaited_once()


@pytest.mark.asyncio
async def test_last_vote_resolves_the_round_and_eliminates_the_leader():
    c = _consumer(cid="p3")
    room = _room(
        {
            "p1": _p("A", "Civil"),
            "p2": _p("B", "Undercover"),
            "p3": _p("C", "Civil"),
        },
        votes={"p1": "p2", "p2": "p1"},
    )

    # p3 casts the last vote for p2 -> p2 has 2 votes, p1 has 1.
    await c.handle_vote(room, "p2")

    assert room["players"]["p2"]["alive"] is False
    assert room["votes"] == {}  # cleared for the next round
    # The eliminated player's role is announced.
    assert any("Intrus" in m["text"] for m in room["messages"] if m["is_system"])
    # No threats left -> civils win.
    assert room["state"] == "ended"
    assert room["result"]["winner"] == "civils"


@pytest.mark.asyncio
async def test_tie_eliminates_nobody_and_triggers_a_revote():
    c = _consumer()
    room = _room(
        {"p1": _p("A"), "p2": _p("B"), "p3": _p("C", "Undercover")},
        votes={"p1": "p2", "p2": "p1"},
    )

    await c.resolve_votes(room)

    assert all(p["alive"] for p in room["players"].values())
    assert room["votes"] == {}
    assert any("Égalité" in m["text"] for m in room["messages"])
    assert room["state"] == "playing"


@pytest.mark.asyncio
async def test_resolve_without_any_valid_vote_is_a_no_op_round():
    c = _consumer()
    room = _room({"p1": _p("A"), "p2": _p("B", "Undercover")}, votes={"p1": "ghost"})

    await c.resolve_votes(room)

    assert all(p["alive"] for p in room["players"].values())
    assert room["state"] == "playing"


@pytest.mark.asyncio
async def test_surviving_round_increments_the_round_counter():
    c = _consumer(cid="p4")
    room = _room(
        {
            "p1": _p("A", "Civil"),
            "p2": _p("B", "Civil"),
            "p3": _p("C", "Civil"),
            "p4": _p("D", "Undercover"),
            "p5": _p("E", "Undercover"),
        },
        votes={"p1": "p3", "p2": "p3", "p3": "p1", "p5": "p3"},
        round=1,
    )

    # p3 (a Civil) is voted out; threats 2 vs civils 2 -> parity, threats win.
    await c.handle_vote(room, "p3")

    assert room["players"]["p3"]["alive"] is False
    assert room["result"]["winner"] == "infiltres"


# --------------------------------------------------------------------------- #
# Mr. White guess
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_eliminated_mrwhite_gets_a_guess_before_the_game_resumes():
    c = _consumer(cid="p3")
    room = _room(
        {
            "p1": _p("A", "Civil"),
            "p2": _p("B", "Civil"),
            "p3": _p("C", "Civil"),
            "p4": _p("D", "MrWhite"),
            "p5": _p("E", "Undercover"),
        },
        votes={"p1": "p4", "p2": "p4", "p4": "p1", "p5": "p1"},
    )

    await c.handle_vote(room, "p4")  # last vote -> p4 (MrWhite) eliminated

    assert room["players"]["p4"]["alive"] is False
    assert room["state"] == "mrwhite_guess"
    assert room["pending_white"] == "p4"


@pytest.mark.asyncio
async def test_correct_mrwhite_guess_wins_the_game_alone():
    c = _consumer(cid="p4")
    room = _room(
        {"p1": _p("A", "Civil"), "p4": _p("D", "MrWhite", alive=False)},
        state="mrwhite_guess",
        pending_white="p4",
    )

    await c.handle_mrwhite_guess(room, "naruto")  # fuzzy match on "Naruto"

    assert room["state"] == "ended"
    assert room["result"]["winner"] == "mrwhite"
    assert room["result"]["reason"] == "guess"
    assert room["result"]["mrwhite_winners"] == ["D"]


@pytest.mark.asyncio
async def test_wrong_mrwhite_guess_resumes_play():
    c = _consumer(cid="p4")
    room = _room(
        {
            "p1": _p("A", "Civil"),
            "p2": _p("B", "Civil"),
            "p3": _p("C", "Undercover"),
            "p4": _p("D", "MrWhite", alive=False),
        },
        state="mrwhite_guess",
        pending_white="p4",
        round=2,
    )

    await c.handle_mrwhite_guess(room, "One Piece")

    assert room["state"] == "playing"
    assert room["pending_white"] is None
    assert room["round"] == 3
    assert any("s'est trompé" in m["text"] for m in room["messages"])


@pytest.mark.asyncio
async def test_wrong_mrwhite_guess_can_still_end_the_game_on_parity():
    c = _consumer(cid="p3")
    room = _room(
        {
            "p1": _p("A", "Civil"),
            "p2": _p("B", "Undercover"),
            "p3": _p("C", "MrWhite", alive=False),
        },
        state="mrwhite_guess",
        pending_white="p3",
    )

    await c.handle_mrwhite_guess(room, "wrong")

    # 1 threat (the Undercover) vs 1 civil -> parity: the infiltrators win.
    assert room["state"] == "ended"
    assert room["result"]["winner"] == "infiltres"


@pytest.mark.asyncio
async def test_guess_from_someone_who_is_not_the_pending_white_is_ignored():
    c = _consumer(cid="p1")
    room = _room(
        {"p1": _p("A", "Civil"), "p4": _p("D", "MrWhite", alive=False)},
        state="mrwhite_guess",
        pending_white="p4",
    )

    await c.handle_mrwhite_guess(room, "Naruto")

    assert room["state"] == "mrwhite_guess"
    assert room["pending_white"] == "p4"
    c.save_room.assert_not_called()


# --------------------------------------------------------------------------- #
# Lobby reset + game start
# --------------------------------------------------------------------------- #
def test_back_to_lobby_clears_roles_and_revives_everyone():
    c = _consumer()
    room = _room(
        {"p1": _p("A", "Civil"), "p2": _p("B", "Undercover", alive=False)},
        state="ended",
        round=4,
        result={"winner": "civils"},
        messages=[{"user": "", "text": "x", "is_system": True}],
    )

    c._reset_to_lobby(room)

    assert room["state"] == "lobby"
    assert room["round"] == 0
    assert room["result"] is None
    assert room["civil_word"] == "" and room["undercover_word"] == ""
    assert room["messages"] == []
    for p in room["players"].values():
        assert p["alive"] is True
        assert p["role"] is None and p["word"] is None


@pytest.mark.asyncio
async def test_start_game_caps_threats_so_civils_keep_the_majority():
    c = _consumer()
    # 4 players but the host asked for 3 undercovers + 2 Mr. Whites.
    room = _room(
        {f"p{i}": _p(f"P{i}") for i in range(1, 5)},
        state="lobby",
        num_undercovers=3,
        num_mrwhites=2,
    )

    game_service = MagicMock()
    game_service.start_undercover_game.return_value = {
        "assignments": {
            cid: {"role": "Civil", "word": "Naruto", "image": None}
            for cid in room["players"]
        },
        "civil_word": "Naruto",
        "undercover_word": "Sasuke",
    }
    container = MagicMock()
    container.core.game_service.return_value = game_service

    with patch.object(uc, "get_container", return_value=container):
        await c.start_game_logic(room)

    # _max_threats(4) == 1 -> 1 undercover, 0 Mr. White (the cap eats the rest).
    kwargs = game_service.start_undercover_game.call_args.kwargs
    assert kwargs["num_undercovers"] == 1
    assert kwargs["num_mrwhites"] == 0
    assert room["state"] == "playing"
    assert room["round"] == 1
    assert room["civil_word"] == "Naruto"


@pytest.mark.asyncio
async def test_start_game_aborts_when_the_service_returns_nothing():
    c = _consumer()
    room = _room({f"p{i}": _p(f"P{i}") for i in range(1, 5)}, state="lobby")

    game_service = MagicMock()
    game_service.start_undercover_game.return_value = None
    container = MagicMock()
    container.core.game_service.return_value = game_service

    with patch.object(uc, "get_container", return_value=container):
        await c.start_game_logic(room)

    # No catalog data -> the room stays in the lobby rather than starting broken.
    assert room["state"] == "lobby"
    c.save_room.assert_not_called()
