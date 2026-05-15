import orjson
import logging
import os
from typing import Dict, Any, Callable, Optional
import time

logger = logging.getLogger('animetix')

class MultiAgentBus:
    """
    Système de Communication Inter-Agents (Shared Memory & Binary Protocol).
    Optimise la communication entre les agents (RAG, Vision, Graph, etc.)
    en utilisant Redis comme mémoire partagée et orjson pour une sérialisation binaire rapide.
    """
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url
        self._redis_client = None
        self._shared_memory_store = {} # Fallback in-memory
        self._subscribers = {}
        self.message_counter = 0
        
        if self.redis_url:
            try:
                import redis
                self._redis_client = redis.from_url(self.redis_url)
                logger.info("🚀 MultiAgentBus: Connected to Redis for Shared Memory communication.")
            except ImportError:
                logger.warning("⚠️ Redis package not found. Falling back to in-memory shared store.")
            except Exception as e:
                logger.error(f"❌ Failed to connect to Redis: {e}")

    def register_agent(self, agent_id: str, callback: Callable):
        """Enregistre un agent sur le bus d'événements."""
        self._subscribers[agent_id] = callback
        logger.info(f"🔌 Agent '{agent_id}' connected to MultiAgentBus.")

    def publish_binary_message(self, sender_id: str, target_id: str, action: str, payload: Dict[str, Any]) -> str:
        """
        Envoie un message binaire optimisé d'un agent à un autre via shared memory.
        """
        start_time = time.perf_counter()
        
        # 1. Sérialisation binaire ultra-rapide via orjson
        binary_payload = orjson.dumps(payload)
        
        # 2. Identifiant unique du message
        msg_id = f"animetix:bus:msg:{int(time.time()*1000)}_{self.message_counter}"
        self.message_counter += 1
        
        # 3. Stockage dans la mémoire partagée (Redis ou Local)
        msg_envelope = {
            "sender": sender_id,
            "target": target_id,
            "action": action,
            "timestamp": time.time()
        }
        
        if self._redis_client:
            # On utilise Redis HSET pour l'enveloppe et SET pour le payload binaire (Blob)
            self._redis_client.set(f"{msg_id}:payload", binary_payload, ex=60) # TTL 60s
            self._redis_client.hset(msg_id, mapping=msg_envelope)
            self._redis_client.expire(msg_id, 60)
        else:
            msg_envelope["payload"] = binary_payload
            self._shared_memory_store[msg_id] = msg_envelope
        
        # 4. Notification Zero-Copy : On envoie uniquement l'ID mémoire
        if target_id in self._subscribers:
            # En environnement multi-processus, ceci utiliserait Redis Pub/Sub ou Signaux
            self._subscribers[target_id](msg_id)
            
        latency = (time.perf_counter() - start_time) * 1000
        logger.debug(f"⚡ Inter-Agent Bus: {sender_id} -> {target_id} [{action}] in {latency:.3f}ms")
        
        return msg_id

    def read_shared_memory(self, msg_id: str) -> Dict[str, Any]:
        """Récupère et désérialise les données depuis la mémoire partagée."""
        if self._redis_client:
            binary_payload = self._redis_client.get(f"{msg_id}:payload")
            if not binary_payload: return {}
            return orjson.loads(binary_payload)
        else:
            msg = self._shared_memory_store.get(msg_id)
            if not msg: return {}
            return orjson.loads(msg["payload"])
            
    def cleanup(self, msg_id: str):
        """Libère la mémoire après lecture si nécessaire."""
        if self._redis_client:
            self._redis_client.delete(msg_id, f"{msg_id}:payload")
        else:
            self._shared_memory_store.pop(msg_id, None)
