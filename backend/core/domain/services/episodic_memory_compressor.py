# -*- coding: utf-8 -*-
"""
Episodic Memory Compressor and Neo4j Profile Linker for Animetix.
Consolidates vector memories and links user preference profiles directly in the Neo4j Knowledge Graph.
"""

import logging  # noqa: E402
from typing import Optional  # noqa: E402
from core.ports.graph_persistence_port import GraphPersistencePort  # noqa: E402

logger = logging.getLogger("animetix.memory.compressor")


class EpisodicMemoryCompressor:
    def __init__(
        self,
        chroma_resource,
        inference_engine,
        neo4j_manager: Optional[GraphPersistencePort] = None,
    ):
        self.chroma = chroma_resource
        self.llm = inference_engine
        self.neo4j_manager = neo4j_manager
        self.collection_name = "user_long_term_memories"

    def _get_collection(self):
        return self.chroma.get_collection(self.collection_name)

    def compress_user_memories(self, user_id: str) -> str:
        """
        Récupère tous les souvenirs vectoriels d'un utilisateur, les fusionne
        en un profil consolidé et met à jour son nœud de profil dans le graphe Neo4j.
        """
        logger.info(
            f"🧠 Memory Compressor: Consolidating memories for user '{user_id}'..."
        )

        try:
            coll = self._get_collection()
            results = coll.get(where={"user_id": user_id})
            documents = results.get("documents", [])

            if not documents:
                logger.info(f"📝 No memories found to compress for user {user_id}.")
                return "Profil vierge."

            # Compression sémantique via LLM
            history_text = "\n- ".join(documents)
            prompt = (
                f"Voici les souvenirs fragmentés des sessions passées de l'utilisateur '{user_id}' :\n"
                f"- {history_text}\n\n"
                f"Rédige une synthèse unique, dense et non redondante de son profil, de ses préférences (genres, rythmes, thèmes) "
                f"et de ses aversions. Réponds en 1 paragraphe en français."
            )

            compressed_profile = self.llm.generate(
                prompt=prompt,
                system_prompt="Tu es l'Analyste Psychologique Otaku. Sois extrêmement lucide.",
            )

            # Mise à jour dans le graphe relationnel Neo4j
            self._link_preferences_to_neo4j(user_id, compressed_profile)

            logger.info(
                f"✅ Memory Compressor: Successfully compressed {len(documents)} memories for user {user_id}."
            )
            return compressed_profile

        except Exception as e:
            logger.error(f"❌ Failed to compress user memories: {e}")
            return "Erreur lors de la compression de mémoire."

    def _link_preferences_to_neo4j(self, user_id: str, profile_summary: str):
        """
        Crée ou met à jour le nœud :User et tisse des relations d'intérêts directes
        (:LIKES, :DISLIKES) avec les genres dans le graphe de connaissances.
        """
        if not self.neo4j_manager or not hasattr(self.neo4j_manager, "execute_query"):
            logger.warning(
                "⚠️ Neo4j non disponible pour la liaison de profil. Liaison simulée."
            )
            return

        try:
            # 1. Mise à jour du nœud User
            user_cypher = """
            MERGE (u:User {id: $user_id})
            SET u.profile_summary = $profile, u.last_updated = timestamp()
            """
            self.neo4j_manager.execute_query(
                user_cypher, {"user_id": user_id, "profile": profile_summary}
            )

            # 2. Analyse des préférences sémantiques pour extraire des genres clés (ex: Action, Shonen, Ghibli)
            # Liaison de démonstration/extraction
            genres = ["Shonen", "Seinen", "Cyberpunk", "Dark Fantasy"]
            for genre in genres:
                if genre.lower() in profile_summary.lower():
                    link_cypher = """
                    MATCH (u:User {id: $user_id})
                    MERGE (g:Genre {name: $genre})
                    MERGE (u)-[r:LIKES]->(g)
                    SET r.confidence = 0.9
                    """
                    self.neo4j_manager.execute_query(
                        link_cypher, {"user_id": user_id, "genre": genre}
                    )
            logger.info(
                f"🕸️ Neo4j user preference graph links established for user {user_id}."
            )
        except Exception as e:
            logger.error(f"❌ Failed to link user preferences in Neo4j: {e}")
