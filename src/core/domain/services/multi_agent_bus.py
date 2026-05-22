import asyncio
import orjson
import logging
import os
import json
from typing import Dict, Any, Callable, Optional, Union
import time

# --- STRUCTURED LOGGING FOR LOKI ---
logger = logging.getLogger('animetix.bus')

class LokiJSONFormatter(logging.Formatter):
    """Formateur JSON pour Grafana Loki."""
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "bus_event"):
            log_data["event"] = record.bus_event
        return json.dumps(log_data)

# Configuration du logger structuré
bus_handler = logging.StreamHandler()
bus_handler.setFormatter(LokiJSONFormatter())
logger.handlers = [bus_handler]
logger.propagate = False

class MultiAgentBus:
    """
    Système de Communication Inter-Agents (Shared Memory & Binary Protocol).
    Optimise la communication entre les agents (RAG, Vision, Graph, etc.)
    en utilisant Redis asynchrone comme mémoire partagée et Pub/Sub pour les notifications.
    """
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url
        self._redis_client = None
        self._shared_memory_store = {} # Fallback in-memory
        self._subscribers = {}
        self._listen_tasks: Dict[str, asyncio.Task] = {}
        self.message_counter = 0
        
        if self.redis_url:
            try:
                import redis.asyncio as aredis
                self._redis_client = aredis.from_url(self.redis_url)
                logger.info("Connected to Async Redis for Shared Memory communication.", extra={"bus_event": {"type": "system", "status": "connected"}})
            except ImportError:
                logger.warning("redis.asyncio not found. Falling back to in-memory shared store.", extra={"bus_event": {"type": "system", "status": "fallback"}})
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}", extra={"bus_event": {"type": "system", "status": "error"}})

    async def _listen_loop(self, agent_id: str, callback: Callable):
        """Boucle d'écoute asynchrone pour un agent via Redis Pub/Sub."""
        channel = f"animetix:bus:agent:{agent_id}"
        pubsub = self._redis_client.pubsub()
        await pubsub.subscribe(channel)
        
        logger.debug(f"Agent listening on channel '{channel}'", extra={"bus_event": {"type": "listen", "agent_id": agent_id}})
        
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message and message['type'] == 'message':
                    msg_id = message['data'].decode('utf-8') if isinstance(message['data'], bytes) else message['data']
                    
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(msg_id)
                        else:
                            callback(msg_id)
                    except Exception as callback_err:
                        logger.error(f"Callback error for agent: {callback_err}", extra={"bus_event": {"type": "callback_error", "agent_id": agent_id, "msg_id": msg_id}})
                
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            logger.info(f"Stopped listening for agent '{agent_id}'")
        except Exception as e:
            logger.error(f"Error in listen loop for agent '{agent_id}': {e}")
        finally:
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
            except Exception:
                pass

    def register_agent(self, agent_id: str, callback: Callable):
        """Enregistre un agent sur le bus d'événements."""
        self._subscribers[agent_id] = callback

        if self._redis_client:
            if agent_id in self._listen_tasks:
                self._listen_tasks[agent_id].cancel()

            try:
                loop = asyncio.get_running_loop()
                task = loop.create_task(self._listen_loop(agent_id, callback))
                self._listen_tasks[agent_id] = task
            except RuntimeError:
                pass

        logger.info(f"Agent '{agent_id}' registered on MultiAgentBus.", extra={"bus_event": {"type": "registration", "agent_id": agent_id}})

    async def publish_binary_message(self, sender_id: str, target_id: str, action: str, payload: Dict[str, Any]) -> str:
        """
        Envoie un message binaire optimisé d'un agent à un autre via shared memory.
        """
        start_time = time.perf_counter()
        binary_payload = orjson.dumps(payload)
        msg_id = f"animetix:bus:msg:{int(time.time()*1000)}_{self.message_counter}"
        self.message_counter += 1
        
        msg_envelope = {
            "sender": sender_id,
            "target": target_id,
            "action": action,
            "timestamp": time.time()
        }
        
        if self._redis_client:
            await self._redis_client.set(f"{msg_id}:payload", binary_payload, ex=60)
            await self._redis_client.hset(msg_id, mapping=msg_envelope)
            await self._redis_client.expire(msg_id, 60)
            
            channel = f"animetix:bus:agent:{target_id}"
            await self._redis_client.publish(channel, msg_id)
        else:
            msg_envelope["payload"] = binary_payload
            self._shared_memory_store[msg_id] = msg_envelope
            
            if target_id in self._subscribers:
                callback = self._subscribers[target_id]
                if asyncio.iscoroutinefunction(callback):
                    await callback(msg_id)
                else:
                    callback(msg_id)
            
        latency = (time.perf_counter() - start_time) * 1000
        
        # LOGGING STRUCTURÉ POUR LOKI
        logger.debug(
            f"Message: {sender_id} -> {target_id} [{action}]",
            extra={"bus_event": {
                "type": "publish",
                "sender": sender_id,
                "target": target_id,
                "action": action,
                "latency_ms": round(latency, 3),
                "msg_id": msg_id
            }}
        )
        
        return msg_id

    async def read_shared_memory(self, msg_id: str) -> Dict[str, Any]:
        """Récupère et désérialise les données depuis la mémoire partagée."""
        if self._redis_client:
            binary_payload = await self._redis_client.get(f"{msg_id}:payload")
            if not binary_payload: return {}
            return orjson.loads(binary_payload)
        else:
            msg = self._shared_memory_store.get(msg_id)
            if not msg: return {}
            return orjson.loads(msg["payload"])
            
    async def cleanup(self, msg_id: str):
        """Libère la mémoire après lecture si nécessaire."""
        if self._redis_client:
            await self._redis_client.delete(msg_id, f"{msg_id}:payload")
        else:
            self._shared_memory_store.pop(msg_id, None)

    async def close(self):
        """Ferme les connexions et arrête les tâches de fond."""
        for task in self._listen_tasks.values():
            task.cancel()
        
        if self._redis_client:
            await self._redis_client.close()
        
        logger.info("MultiAgentBus shutdown complete.", extra={"bus_event": {"type": "system", "status": "shutdown"}})
