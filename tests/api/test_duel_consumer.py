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


def _patch_container(mocker, is_correct=False, raw_similarity=0.0):
    """Patch ``get_container`` in the duel module to a structured mock.

    Mirrors the real access path: ``container.core.catalog_service.load_data`` and
    ``container.core.game_service.{check_title_match, calculate_raw_similarity}``.
    These are sync callables (the consumer wraps them in ``sync_to_async``).
    """
    container = MagicMock()
    container.core.catalog_service.return_value.load_data.return_value = {
        "title_to_full_data": {"Naruto": {"id": 1, "title": "Naruto"}}
    }
    container.core.game_service.return_value.check_title_match.return_value = is_correct
    container.core.game_service.return_value.calculate_raw_similarity.return_value = (
        raw_similarity
    )
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

    # No similarity scoring on a win.
    container.core.game_service.return_value.calculate_raw_similarity.assert_not_called()

    # Broadcast announces the winner and reveals the secret.
    group, message = _last_group_send_message(consumer.channel_layer)
    assert group == consumer.room_group_name
    assert message == {
        "type": "duel_finished",
        "winner": "p1",
        "secret": "Naruto",
    }


async def test_handle_guess_wrong_broadcasts_similarity_score_without_finishing(mocker):
    """A wrong guess: duel stays open, no reward, broadcast carries a rounded score."""
    player = _make_user("p2")
    duel = _make_duel(secret="Naruto", media_type="Anime", is_finished=False)
    _patch_duelroom(mocker, get_return=duel)
    # 0.8123 -> round(81.23, 1) == 81.2
    container = _patch_container(mocker, is_correct=False, raw_similarity=0.8123)
    consumer = _make_consumer(player)

    await consumer.handle_guess("Bleach")

    # State untouched: not finished, no winner, not saved, no reward.
    assert duel.is_finished is False
    assert duel.winner is None
    duel.save.assert_not_called()
    player.profile.add_win.assert_not_called()

    # Similarity computed against the secret with the loaded data set.
    container.core.game_service.return_value.calculate_raw_similarity.assert_called_once_with(
        "Anime",
        "Naruto",
        "Bleach",
        {"title_to_full_data": {"Naruto": {"id": 1, "title": "Naruto"}}},
    )

    group, message = _last_group_send_message(consumer.channel_layer)
    assert group == consumer.room_group_name
    assert message == {
        "type": "opponent_guess",
        "player": "p2",
        "score": 81.2,
    }


async def test_handle_guess_reconciles_turns_between_two_players(mocker):
    """Two players guess the same room: only the correct guesser wins; the other
    receives a score and the win is attributed to the right player."""
    p1, p2 = _make_user("p1"), _make_user("p2")
    duel = _make_duel(
        secret="Naruto", media_type="Anime", player1=p1, player2=p2, is_finished=False
    )
    _patch_duelroom(mocker, get_return=duel)
    container = _patch_container(mocker, is_correct=False, raw_similarity=0.5)

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
