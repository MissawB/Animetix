import pytest
import asyncio
import orjson
from unittest.mock import AsyncMock, patch, MagicMock
from core.domain.services.multi_agent_bus import MultiAgentBus

@pytest.mark.asyncio
async def test_multi_agent_bus_redis_initialization():
    """Vérifie que le bus se connecte à Redis quand une URL est fournie."""
    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_redis = AsyncMock()
        mock_from_url.return_value = mock_redis
        
        bus = MultiAgentBus(redis_url="redis://localhost:6379")
        try:
            assert bus.redis_url == "redis://localhost:6379"
            mock_from_url.assert_called_once_with("redis://localhost:6379")
            assert bus._redis_client == mock_redis
        finally:
            await bus.close()

@pytest.mark.asyncio
async def test_multi_agent_bus_redis_subscription():
    """Vérifie que l'enregistrement d'un agent démarre une tâche d'écoute Redis."""
    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_redis = MagicMock()
        mock_from_url.return_value = mock_redis
        
        mock_pubsub = MagicMock()
        mock_redis.pubsub.return_value = mock_pubsub
        
        # Méthodes asynchrones
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.get_message = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.close = AsyncMock()
        mock_redis.close = AsyncMock()
        
        bus = MultiAgentBus(redis_url="redis://localhost:6379")
        try:
            callback = AsyncMock()
            agent_id = "test_agent"
            
            # Simuler un message arrivant sur Pub/Sub
            mock_pubsub.get_message.side_effect = [
                {'type': 'message', 'data': b'msg_123'},
                None, None, None, None # Laisser la boucle tourner un peu
            ]
            
            bus.register_agent(agent_id, callback)
            
            # Attendre que le callback soit appelé
            for _ in range(20):
                await asyncio.sleep(0.01)
                if callback.called:
                    break
            
            # Vérifications
            assert agent_id in bus._listen_tasks
            mock_pubsub.subscribe.assert_called_with(f"animetix:bus:agent:{agent_id}")
            callback.assert_called_with("msg_123")
        finally:
            await bus.close()

@pytest.mark.asyncio
async def test_multi_agent_bus_redis_publish():
    """Vérifie la publication distribuée via Redis."""
    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_redis = AsyncMock()
        mock_from_url.return_value = mock_redis
        
        bus = MultiAgentBus(redis_url="redis://localhost:6379")
        try:
            payload = {"cmd": "analyze", "target": "image_01"}
            msg_id = await bus.publish_binary_message("agent_vision", "agent_rag", "vision_result", payload)
            
            assert msg_id.startswith("animetix:bus:msg:")
            assert mock_redis.set.called
            mock_redis.publish.assert_called_with(f"animetix:bus:agent:agent_rag", msg_id)
        finally:
            await bus.close()

@pytest.mark.asyncio
async def test_multi_agent_bus_redis_read_shared_memory():
    """Vérifie la lecture depuis la mémoire partagée Redis."""
    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_redis = AsyncMock()
        mock_from_url.return_value = mock_redis
        
        bus = MultiAgentBus(redis_url="redis://localhost:6379")
        try:
            msg_id = "animetix:bus:msg:12345"
            payload = {"data": "secret"}
            mock_redis.get.return_value = orjson.dumps(payload)
            
            result = await bus.read_shared_memory(msg_id)
            
            assert mock_redis.get.called
            assert result == payload
        finally:
            await bus.close()

@pytest.mark.asyncio
async def test_multi_agent_bus_local_fallback_no_redis():
    """Vérifie que le bus fonctionne en mode local si redis_url est None."""
    bus = MultiAgentBus(redis_url=None)
    try:
        assert bus._redis_client is None
        
        callback = AsyncMock()
        bus.register_agent("local_agent", callback)
        
        payload = {"info": "local"}
        msg_id = await bus.publish_binary_message("sender", "local_agent", "action", payload)
        
        callback.assert_called_once_with(msg_id)
        result = await bus.read_shared_memory(msg_id)
        assert result == payload
    finally:
        await bus.close()
