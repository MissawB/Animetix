"""Real-behavior unit tests for ``DuelConsumer`` (Django Channels async consumer).

These tests instantiate ``DuelConsumer`` directly and drive its async methods,
mocking only the I/O boundary (``channel_layer``, ``send``, ``accept``, ``close``)
and the data/service layer (``DuelRoom`` ORM, the DI container's catalog/game
services, and the user's profile reward path). No real DB / redis / network.

They complement the API-level tests in ``test_duel.py`` (which exercise the REST
create/join/matchmaking endpoints) by covering the websocket game logic:
connection gating, group membership, guess routing, win/score reconciliation
and the exact payloads broadcast to the room.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from animetix.consumers import duel as duel_module
from animetix.consumers.duel import DuelConsumer
from core.domain.exceptions import GameLogicError

pytestmark = pytest.mark.asyncio


# --------------------------------------------------------------------------- #
# Helpers / fixtures
# --------------------------------------------------------------------------- #
def _make_user(username="player1", anonymous=False):
    """A stand-in for a Django ``User`` (identity by object, has .username/.profile)."""
    user = MagicMock()
    user.username = username
    user.is_anonymous = anonymous
    # profile.add_win is the reward hook invoked on a win.
    user.profile = MagicMock()
    user.profile.add_win = MagicMock()
    return user


def _make_duel(
    room_code="ABCDE",
    media_type="Anime",
    secret="Naruto",
    player1=None,
    player2=None,
    is_finished=False,
):
    """A stand-in for a ``DuelRoom`` instance with the attributes the consumer reads."""
    duel = MagicMock()
    duel.room_code = room_code
    duel.media_type = media_type
    duel.secret_title = secret
    duel.is_finished = is_finished
    duel.winner = None
    duel.player1 = player1
    duel.player2 = player2
    duel.save = MagicMock()
    return duel


def _patch_duelroom(mocker, get_return=None, get_side_effect=None):
    """Patch ``DuelRoom`` in the models namespace (the consumer imports it lazily).

    Returns the mock class so the test can assert / inspect ``objects.get`` calls.
    """
    import animetix.models as models

    duelroom = MagicMock()
    # Preserve a real-ish DoesNotExist exception class for the except clause.
    duelroom.DoesNotExist = models.DuelRoom.DoesNotExist
    if get_side_effect is not None:
        duelroom.objects.get.side_effect = get_side_effect
    else:
        duelroom.objects.get.return_value = get_return
    mocker.patch.object(models, "DuelRoom", duelroom)
    return duelroom


def _patch_container(mocker, is_correct=False, rank=None, report=None):
    """Patch ``get_container`` in the duel module to a structured mock.

    Mirrors the real access path: ``container.core.catalog_service.load_data``,
    ``container.core.game_service.check_title_match`` and
    ``container.core.proximity_service.{rank, report}`` -- the same percentile
    scoring the classic game uses, instead of the raw (meaningless) cosine.
    These are sync callables (the consumer wraps them in ``sync_to_async``).
    """
    container = MagicMock()
    container.core.catalog_service.return_value.load_data.return_value = {
        "title_to_full_data": {"Naruto": {"id": 1, "title": "Naruto"}}
    }
    container.core.game_service.return_value.check_title_match.return_value = is_correct
    container.core.proximity_service.return_value.rank.return_value = (
        rank if rank is not None else ["Bleach", "One Piece"]
    )
    container.core.proximity_service.return_value.report.return_value = report or {
        "percent": 5.0,
        "rank": 2,
        "total": 2,
        "reasons": [],
    }
    mocker.patch.object(duel_module, "get_container", return_value=container)
    return container


def _make_consumer(user, room_code="ABCDE"):
    """Instantiate a consumer wired with mocked async I/O and a populated scope."""
    consumer = DuelConsumer()
    consumer.scope = {
        "url_route": {"kwargs": {"lobby_id": room_code}},
        "user": user,
    }
    consumer.channel_name = "test.channel.1"
    # ``room_code`` / ``room_group_name`` / ``user`` are normally assigned in
    # connect(); set them for methods driven directly (handle_guess /
    # broadcast_state) which read them for the ORM lookup and group_send target.
    consumer.room_code = room_code
    consumer.room_group_name = f"duel_{room_code}"
    consumer.user = user
    consumer.channel_layer = AsyncMock()
    consumer.send = AsyncMock()
    consumer.accept = AsyncMock()
    consumer.close = AsyncMock()
    return consumer


def _last_group_send_message(channel_layer):
    """Extract the inner ``message`` dict from the most recent group_send call."""
    args, kwargs = channel_layer.group_send.call_args
    group, event = args
    return group, event["message"]


# --------------------------------------------------------------------------- #
# connect()
# --------------------------------------------------------------------------- #
async def test_connect_rejects_anonymous_user(mocker):
    """Anonymous users are closed out before any DB lookup or group join."""
    duelroom = _patch_duelroom(mocker, get_return=_make_duel())
    user = _make_user(anonymous=True)
    consumer = _make_consumer(user)

    await consumer.connect()

    consumer.close.assert_awaited_once()
    consumer.accept.assert_not_awaited()
    consumer.channel_layer.group_add.assert_not_awaited()
    duelroom.objects.get.assert_not_called()  # never touched the DB


async def test_connect_closes_when_room_missing(mocker):
    """A non-existent room code closes the socket (DoesNotExist branch)."""
    import animetix.models as models

    duelroom = _patch_duelroom(mocker, get_side_effect=models.DuelRoom.DoesNotExist())
    user = _make_user(anonymous=False)
    consumer = _make_consumer(user)

    await consumer.connect()

    consumer.close.assert_awaited_once()
    consumer.accept.assert_not_awaited()
    consumer.channel_layer.group_add.assert_not_awaited()
    assert duelroom.objects.get.called


async def test_connect_rejects_non_participant(mocker):
    """A user who is neither player1 nor player2 is closed out."""
    p1, p2 = _make_user("p1"), _make_user("p2")
    intruder = _make_user("intruder")
    duel = _make_duel(player1=p1, player2=p2)
    _patch_duelroom(mocker, get_return=duel)
    consumer = _make_consumer(intruder)

    await consumer.connect()

    consumer.close.assert_awaited_once()
    consumer.accept.assert_not_awaited()
    consumer.channel_layer.group_add.assert_not_awaited()


async def test_connect_accepts_participant_joins_group_and_broadcasts_state(mocker):
    """A valid participant: joins the group, accepts, then broadcasts duel_state."""
    p1, p2 = _make_user("p1"), _make_user("p2")
    duel = _make_duel(
        room_code="ROOM1", media_type="Manga", player1=p1, player2=p2, is_finished=False
    )
    _patch_duelroom(mocker, get_return=duel)
    consumer = _make_consumer(p1, room_code="ROOM1")

    await consumer.connect()

    # Group derived from room code, joined with this channel, then accepted.
    assert consumer.room_group_name == "duel_ROOM1"
    consumer.channel_layer.group_add.assert_awaited_once_with(
        "duel_ROOM1", "test.channel.1"
    )
    consumer.accept.assert_awaited_once()
    consumer.close.assert_not_awaited()

    # connect() ends by broadcasting the initial state to the room.
    group, message = _last_group_send_message(consumer.channel_layer)
    assert group == "duel_ROOM1"
    assert message == {
        "type": "duel_state",
        "player1": "p1",
        "player2": "p2",
        "media_type": "Manga",
        "is_finished": False,
    }


# --------------------------------------------------------------------------- #
# disconnect()
# --------------------------------------------------------------------------- #
async def test_disconnect_leaves_group(mocker):
    """disconnect() removes this channel from the room group."""
    consumer = _make_consumer(_make_user())
    consumer.room_group_name = "duel_ROOM1"

    await consumer.disconnect(close_code=1000)

    consumer.channel_layer.group_discard.assert_awaited_once_with(
        "duel_ROOM1", "test.channel.1"
    )


# --------------------------------------------------------------------------- #
# receive() routing
# --------------------------------------------------------------------------- #
async def test_receive_routes_guess_action_to_handle_guess(mocker):
    """A ``{"type": "guess", "guess": ...}`` frame is dispatched to handle_guess."""
    consumer = _make_consumer(_make_user())
    consumer.handle_guess = AsyncMock()

    await consumer.receive(text_data=json.dumps({"type": "guess", "guess": "Bleach"}))

    consumer.handle_guess.assert_awaited_once_with("Bleach")


async def test_receive_ignores_unknown_action(mocker):
    """An unrecognised action type is a silent no-op (no handler invoked)."""
    consumer = _make_consumer(_make_user())
    consumer.handle_guess = AsyncMock()

    await consumer.receive(text_data=json.dumps({"type": "chat", "message": "hi"}))

    consumer.handle_guess.assert_not_awaited()
    consumer.channel_layer.group_send.assert_not_awaited()


# --------------------------------------------------------------------------- #
# handle_guess()
# --------------------------------------------------------------------------- #
async def test_handle_guess_noop_when_duel_already_finished(mocker):
    """No scoring or broadcast happens once the duel is finished."""
    duel = _make_duel(is_finished=True)
    _patch_duelroom(mocker, get_return=duel)
    container = _patch_container(mocker)
    consumer = _make_consumer(_make_user())

    await consumer.handle_guess("Naruto")

    consumer.channel_layer.group_send.assert_not_awaited()
    duel.save.assert_not_called()
    container.core.game_service.return_value.check_title_match.assert_not_called()


async def test_handle_guess_correct_finishes_duel_and_broadcasts_winner(mocker):
    """A correct guess: marks finished, records winner, rewards, broadcasts result."""
    winner = _make_user("p1")
    duel = _make_duel(secret="Naruto", media_type="Anime", is_finished=False)
    _patch_duelroom(mocker, get_return=duel)
    container = _patch_container(mocker, is_correct=True)
    consumer = _make_consumer(winner)

    await consumer.handle_guess("Naruto")

    # Real state transition persisted.
    assert duel.is_finished is True
    assert duel.winner is winner
    duel.save.assert_called_once()

    # check_title_match was given the secret's full data, not the bare title.
    container.core.game_service.return_value.check_title_match.assert_called_once_with(
        "Naruto", {"id": 1, "title": "Naruto"}
    )

    # Reward path fired with the right game mode / media type.
    winner.profile.add_win.assert_called_once_with(game_mode="duel", media_type="Anime")

    # No proximity scoring on a win.
    container.core.proximity_service.return_value.rank.assert_not_called()
    container.core.proximity_service.return_value.report.assert_not_called()

    # Broadcast announces the winner and reveals the secret.
    group, message = _last_group_send_message(consumer.channel_layer)
    assert group == consumer.room_group_name
    assert message == {
        "type": "duel_finished",
        "winner": "p1",
        "secret": "Naruto",
    }


async def test_handle_guess_wrong_broadcasts_proximity_percent_without_finishing(
    mocker,
):
    """A wrong guess: duel stays open, no reward, broadcast carries the
    ProximityService percentile (NOT the raw cosine -- that's the whole point of
    this fix)."""
    player = _make_user("p2")
    duel = _make_duel(secret="Naruto", media_type="Anime", is_finished=False)
    _patch_duelroom(mocker, get_return=duel)
    container = _patch_container(
        mocker,
        is_correct=False,
        rank=["Bleach", "One Piece"],
        report={"percent": 81.2, "rank": 1, "total": 2, "reasons": []},
    )
    consumer = _make_consumer(player)

    await consumer.handle_guess("Bleach")

    # State untouched: not finished, no winner, not saved, no reward.
    assert duel.is_finished is False
    assert duel.winner is None
    duel.save.assert_not_called()
    player.profile.add_win.assert_not_called()

    # Ranking computed against the secret, report computed for this guess.
    container.core.proximity_service.return_value.rank.assert_called_once_with(
        "Anime", "Naruto"
    )
    container.core.proximity_service.return_value.report.assert_called_once_with(
        "Anime", "Naruto", "Bleach", ranking=["Bleach", "One Piece"]
    )

    group, message = _last_group_send_message(consumer.channel_layer)
    assert group == consumer.room_group_name
    assert message == {
        "type": "opponent_guess",
        "player": "p2",
        "score": 81.2,
    }


async def test_handle_guess_with_no_relationship_scores_low_not_the_noise_floor(mocker):
    """The regression this fix closes: with the 0.7 cosine factor gone, an
    unrelated guess used to render at the raw-cosine noise floor (~58 on the real
    catalogue -- the average for two works with NO relationship). The percentile
    from ProximityService must instead put a no-signal guess near the BOTTOM of
    the ranking, never in the high 50s reading as "getting warm"."""
    player = _make_user("p2")
    duel = _make_duel(secret="Naruto", media_type="Anime", is_finished=False)
    _patch_duelroom(mocker, get_return=duel)
    # An unrelated title ranked dead last out of 100 -> percentile near 0, not ~58.
    _patch_container(
        mocker,
        is_correct=False,
        rank=["Unrelated Title"] + [f"Title {i}" for i in range(99)],
        report={"percent": 1.0, "rank": 100, "total": 100, "reasons": []},
    )
    consumer = _make_consumer(player)

    await consumer.handle_guess("Unrelated Title")

    _, message = _last_group_send_message(consumer.channel_layer)
    assert message["type"] == "opponent_guess"
    assert message["score"] < 50.0  # nowhere near the old ~58 noise floor
    assert message["score"] == 1.0


async def test_handle_guess_caches_ranking_once_per_room_not_once_per_guess(mocker):
    """The ranking is expensive (whole-catalogue comparison): computed once per
    room and re-read from cache on every subsequent guess, exactly like the
    classic game caches it once per game."""
    from django.core.cache import cache

    player = _make_user("p2")
    duel = _make_duel(secret="Naruto", media_type="Anime", is_finished=False)
    _patch_duelroom(mocker, get_return=duel)
    container = _patch_container(
        mocker,
        is_correct=False,
        rank=["Bleach", "One Piece"],
        report={"percent": 5.0, "rank": 2, "total": 2, "reasons": []},
    )
    consumer = _make_consumer(player)

    await consumer.handle_guess("Bleach")
    await consumer.handle_guess("One Piece")

    # rank() is the expensive whole-catalogue computation -- called once, not twice.
    container.core.proximity_service.return_value.rank.assert_called_once_with(
        "Anime", "Naruto"
    )
    assert container.core.proximity_service.return_value.report.call_count == 2
    cache.clear()


async def test_handle_guess_proximity_unavailable_sends_error_not_crash(mocker):
    """GameLogicError (no exploitable proximity signal for this media type) must
    not crash the socket. It's handled like the classic game's 503: a clean error
    is sent to the guessing player only, the duel is left open, and nothing is
    broadcast to the room."""
    player = _make_user("p2")
    duel = _make_duel(secret="Naruto", media_type="Anime", is_finished=False)
    _patch_duelroom(mocker, get_return=duel)
    container = _patch_container(mocker, is_correct=False)
    container.core.proximity_service.return_value.rank.side_effect = GameLogicError(
        "no signal for this catalogue"
    )
    consumer = _make_consumer(player)

    await consumer.handle_guess("Bleach")  # must not raise

    # No broadcast to the room -- the error is only for the player who guessed.
    consumer.channel_layer.group_send.assert_not_awaited()
    consumer.send.assert_awaited_once()
    sent = json.loads(consumer.send.await_args.kwargs["text_data"])
    assert sent["type"] == "error"

    # Duel state untouched -- a scoring outage isn't a game-ending event.
    assert duel.is_finished is False
    duel.save.assert_not_called()


async def test_handle_guess_reconciles_turns_between_two_players(mocker):
    """Two players guess the same room: only the correct guesser wins; the other
    receives a score and the win is attributed to the right player."""
    p1, p2 = _make_user("p1"), _make_user("p2")
    duel = _make_duel(
        secret="Naruto", media_type="Anime", player1=p1, player2=p2, is_finished=False
    )
    _patch_duelroom(mocker, get_return=duel)
    container = _patch_container(
        mocker,
        is_correct=False,
        rank=["Bleach", "One Piece"],
        report={"percent": 5.0, "rank": 2, "total": 2, "reasons": []},
    )

    # p1 guesses wrong first -> opponent_guess for p1, duel still open.
    consumer1 = _make_consumer(p1)
    await consumer1.handle_guess("Bleach")
    _, msg1 = _last_group_send_message(consumer1.channel_layer)
    assert msg1["type"] == "opponent_guess"
    assert msg1["player"] == "p1"
    assert duel.is_finished is False
    p1.profile.add_win.assert_not_called()

    # Now p2 guesses correctly -> duel finishes, winner is p2 (not p1).
    container.core.game_service.return_value.check_title_match.return_value = True
    consumer2 = _make_consumer(p2)
    await consumer2.handle_guess("Naruto")
    _, msg2 = _last_group_send_message(consumer2.channel_layer)
    assert msg2 == {"type": "duel_finished", "winner": "p2", "secret": "Naruto"}
    assert duel.is_finished is True
    assert duel.winner is p2
    p2.profile.add_win.assert_called_once()
    p1.profile.add_win.assert_not_called()


# --------------------------------------------------------------------------- #
# broadcast_state()
# --------------------------------------------------------------------------- #
async def test_broadcast_state_includes_both_players_when_present(mocker):
    """duel_state carries both usernames, media type and the finished flag."""
    p1, p2 = _make_user("alice"), _make_user("bob")
    duel = _make_duel(media_type="Anime", player1=p1, player2=p2, is_finished=False)
    _patch_duelroom(mocker, get_return=duel)
    consumer = _make_consumer(p1)
    consumer.room_group_name = "duel_ROOM1"

    await consumer.broadcast_state()

    group, message = _last_group_send_message(consumer.channel_layer)
    assert group == "duel_ROOM1"
    assert message == {
        "type": "duel_state",
        "player1": "alice",
        "player2": "bob",
        "media_type": "Anime",
        "is_finished": False,
    }


async def test_broadcast_state_player2_none_when_unjoined(mocker):
    """Before an opponent joins, player2 is reported as None (not an error)."""
    p1 = _make_user("alice")
    duel = _make_duel(media_type="Manga", player1=p1, player2=None, is_finished=False)
    _patch_duelroom(mocker, get_return=duel)
    consumer = _make_consumer(p1)
    consumer.room_group_name = "duel_ROOM1"

    await consumer.broadcast_state()

    _, message = _last_group_send_message(consumer.channel_layer)
    assert message["player1"] == "alice"
    assert message["player2"] is None
    assert message["media_type"] == "Manga"
