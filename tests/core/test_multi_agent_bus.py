import pytest
from unittest.mock import MagicMock
from core.domain.services.multi_agent_bus import MultiAgentBus

@pytest.fixture
def bus():
    # Test with in-memory store
    return MultiAgentBus(redis_url=None)

def test_register_agent(bus):
    callback = MagicMock()
    bus.register_agent("agent1", callback)
    assert "agent1" in bus._subscribers

def test_publish_and_read_message(bus):
    callback = MagicMock()
    bus.register_agent("target", callback)
    
    payload = {"data": "hello"}
    msg_id = bus.publish_binary_message("sender", "target", "test_action", payload)
    
    # Callback should have been called with msg_id
    callback.assert_called_once_with(msg_id)
    
    # Read message
    read_payload = bus.read_shared_memory(msg_id)
    assert read_payload == payload

def test_cleanup(bus):
    msg_id = bus.publish_binary_message("s", "t", "a", {"d": 1})
    assert msg_id in bus._shared_memory_store
    bus.cleanup(msg_id)
    assert msg_id not in bus._shared_memory_store

def test_read_non_existent(bus):
    assert bus.read_shared_memory("invalid") == {}
