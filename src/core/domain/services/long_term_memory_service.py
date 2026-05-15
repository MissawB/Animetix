import logging
from typing import List, Dict, Any, Optional
import datetime

logger = logging.getLogger('animetix')

class LongTermMemoryService:
    """
    Gère la mémoire sémantique à long terme des joueurs.
    Stocke les résumés des parties passées dans ChromaDB pour une personnalisation continue.
    """
    def __init__(self, chroma_resource, inference_engine):
        self.chroma = chroma_resource
        self.llm = inference_engine
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
        prompt = f"Résume les préférences et le style de jeu de cet utilisateur en 2-3 phrases clés pour ta mémoire future :\n\n{history_text}"
        
        try:
            summary = self.llm.generate(prompt, system_prompt="Tu es un système de gestion de mémoire. Sois concis et factuel.")
            
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
        """
        Récupère les souvenirs les plus pertinents par rapport au contexte actuel.
        """
        try:
            coll = self._get_collection()
            # Filtrage par user_id
            results = coll.query(
                query_texts=[current_query],
                n_results=limit,
                where={"user_id": user_id}
            )
            
            memories = results.get('documents', [[]])[0]
            if not memories: return ""
            
            context = "\n- ".join(memories)
            return f"\nSouvenirs de vos échanges passés :\n- {context}\n"
        except Exception as e:
            logger.error(f"❌ Failed to retrieve memories: {e}")
            return ""
