"""Regression lock (silent-except sweep): the Undercover consumer's
public-lobby index registration is best-effort, but its failure must be
logged — a room silently missing from the lobby listing was invisible before.
"""

from unittest.mock import AsyncMock, patch

import pytest
from animetix.consumers import undercover as uc


@pytest.mark.asyncio
async def test_index_add_failure_is_logged_and_swallowed():
    # The module logger is mocked directly because the project logging config
    # does not propagate to the root handler caplog listens on.
    consumer = uc.UndercoverConsumer()
    consumer.room_code = "ROOM42"

    with (
        patch.object(
            uc.state_adapter,
            "get_state",
            AsyncMock(side_effect=RuntimeError("redis down")),
        ),
        patch.object(uc, "logger") as mock_logger,
    ):
        # Must not raise: the room stays joinable by code even if the
        # lobby index update fails.
        await consumer._index_add()

    mock_logger.warning.assert_called_once()
    assert "ROOM42" in mock_logger.warning.call_args.args
    assert mock_logger.warning.call_args.kwargs.get("exc_info") is True
