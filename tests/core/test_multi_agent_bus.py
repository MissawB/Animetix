from unittest.mock import AsyncMock, MagicMock

import pytest
from core.domain.services.multi_agent_bus import MultiAgentBus


@pytest.fixture
def bus():
    # Test with in-memory store
    return MultiAgentBus(redis_url=None)


@pytest.mark.asyncio
async def test_register_agent(bus):
    callback = MagicMock()
    bus.register_agent("agent1", callback)
    assert "agent1" in bus._subscribers
    assert bus._subscribers["agent1"] == callback
    await bus.close()


@pytest.mark.asyncio
async def test_publish_and_read_message(bus):
    callback = AsyncMock()
    bus.register_agent("agent2", callback)

    payload = {"key": "value"}
    msg_id = await bus.publish_binary_message(
        "agent1", "agent2", "test_action", payload
    )

    assert msg_id in bus._shared_memory_store
    callback.assert_called_once_with(msg_id)

    result = await bus.read_shared_memory(msg_id)
    assert result == payload
    await bus.close()


@pytest.mark.asyncio
async def test_cleanup(bus):
    payload = {"k": "v"}
    msg_id = await bus.publish_binary_message("a1", "a2", "act", payload)
    assert msg_id in bus._shared_memory_store
    await bus.cleanup(msg_id)
    assert msg_id not in bus._shared_memory_store
    await bus.close()


@pytest.mark.asyncio
async def test_read_non_existent(bus):
    result = await bus.read_shared_memory("invalid")
    assert result == {}
    await bus.close()


@pytest.mark.asyncio
async def test_close(bus):
    await bus.close()
    # On vérifie juste que ça ne crash pas
