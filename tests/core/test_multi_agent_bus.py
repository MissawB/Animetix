import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
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

@pytest.mark.asyncio
async def test_publish_and_read_message(bus):
    # On utilise AsyncMock car le bus supporte maintenant les callbacks async
    callback = AsyncMock()
    bus.register_agent("target", callback)
    
    payload = {"data": "hello"}
    msg_id = await bus.publish_binary_message("sender", "target", "test_action", payload)
    
    # Callback should have been called with msg_id
    callback.assert_called_once_with(msg_id)
    
    # Read message
    read_payload = await bus.read_shared_memory(msg_id)
    assert read_payload == payload

@pytest.mark.asyncio
async def test_cleanup(bus):
    msg_id = await bus.publish_binary_message("s", "t", "a", {"d": 1})
    assert msg_id in bus._shared_memory_store
    await bus.cleanup(msg_id)
    assert msg_id not in bus._shared_memory_store

@pytest.mark.asyncio
async def test_read_non_existent(bus):
    result = await bus.read_shared_memory("invalid")
    assert result == {}

@pytest.mark.asyncio
async def test_close(bus):
    await bus.close()
    # On vérifie juste que ça ne crash pas
