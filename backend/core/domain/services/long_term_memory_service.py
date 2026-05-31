import logging
from typing import List, Dict, Any, Optional
import datetime
from core.domain.services.prompt_manager import PromptManager

logger = logging.getLogger('animetix')

class LongTermMemoryService:
    """
    Gère la mémoire sémantique à long terme des joueurs.
    Stocke les résumés des parties passées dans ChromaDB pour une personnalisation continue.
    """
    def __init__(self, chroma_resource, inference_engine, prompt_manager: PromptManager):
        self.chroma = chroma_resource
        self.llm = inference_engine
        self.prompt_manager = prompt_manager
        self.collection_name = "user_long_term_memories"

    def _get_collection(self):
        return self.chroma.get_collection(self.collection_name)

    def store_memory(self, user_id: str, conversation_history: List[Dict[str, str]]):
        """
        Résume une session et la stocke comme un 'souvenir' sémantique.
        """
        if not conversation_history: return
        
        # 1. Générer un résumé via le LLM
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in conversation_history])
        prompt, system = self.prompt_manager.get_prompt("long_term_memory_summary", history_text=history_text)
        
        try:
            summary = self.llm.generate(prompt, system_prompt=system)
            
            # 2. Stocker dans Chroma
            coll = self._get_collection()
            timestamp = datetime.datetime.now().isoformat()
            memory_id = f"mem_{user_id}_{timestamp}"
            
            coll.add(
                ids=[memory_id],
                documents=[summary],
                metadatas=[{"user_id": user_id, "date": timestamp}]
            )
            logger.info(f"🧠 Memory stored for user {user_id}")
        except Exception as e:
            logger.error(f"❌ Failed to store memory: {e}")

    def retrieve_relevant_memories(self, user_id: str, current_query: str, limit: int = 3) -> str:
        # ... existing ...

    def get_user_memories(self, user_id: str, limit: int = 10) -> List[str]:
        """
        Récupère les derniers souvenirs d'un utilisateur.
        """
        try:
            coll = self._get_collection()
            results = coll.get(
                where={"user_id": str(user_id)},
                limit=limit
            )
            return results.get('documents', [])
        except Exception as e:
            logger.error(f"❌ Failed to fetch user memories: {e}")
            return []
