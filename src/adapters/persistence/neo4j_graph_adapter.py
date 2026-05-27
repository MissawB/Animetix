import logging
from typing import List, Dict, Any, Optional
from core.ports.graph_persistence_port import GraphPersistencePort
from pipeline.neo4j_client import Neo4jManager

logger = logging.getLogger("animetix.neo4j_adapter")

class Neo4jGraphAdapter(GraphPersistencePort):
    """
    Adapter pour Neo4j implémentant GraphPersistencePort.
    Encapsule Neo4jManager pour respecter l'architecture hexagonale.
    """

    def __init__(self, neo4j_manager: Optional[Neo4jManager] = None):
        self._manager = neo4j_manager or Neo4jManager()

    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return self._manager.execute_query(query, parameters)

    def execute_read(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        # Neo4jManager's execute_query is general, we treat it as read here
        return self._manager.execute_query(query, parameters)

    def execute_write(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> None:
        self._manager.execute_query(query, parameters)

    def find_logical_connections(self, media_id: str) -> List[Dict[str, Any]]:
        return self._manager.find_logical_connections(media_id)

    def get_community_summary(self, category_type: str, category_name: str) -> str:
        return self._manager.get_community_summary(category_type, category_name)

    def multi_hop_traversal(self, start_node: str, steps: List[str]) -> str:
        return self._manager.multi_hop_traversal(start_node, steps)

    def get_enriched_context(self, media_ids: List[str]) -> str:
        return self._manager.get_enriched_context(media_ids)

    def sync_media_to_graph(self, media_item: Any, media_type: str) -> None:
        self._manager.sync_media_to_graph(media_item, media_type)

    def sync_ai_extracted_graph(self, media_id: str, extracted_data: Dict[str, Any]) -> None:
        self._manager.sync_ai_extracted_graph(media_id, extracted_data)

    def sync_fan_theory(self, saga_name: str, theory_data: Dict[str, Any]) -> None:
        self._manager.sync_fan_theory(saga_name, theory_data)

    def sync_saga(self, saga_name: str, executive_summary: str, media_ids: List[str]) -> None:
        self._manager.sync_saga(saga_name, executive_summary, media_ids)

    def sync_combat_lore(self, media_id: str, lore_data_list: List[Dict[str, Any]]) -> None:
        self._manager.sync_combat_lore(media_id, lore_data_list)

    def get_creator_network_context(self, person_name: str) -> str:
        return self._manager.get_creator_network_context(person_name)

    def check_health(self) -> bool:
        if not self._manager.driver:
            return False
        try:
            self._manager.driver.verify_connectivity()
            return True
        except Exception as e:
            logger.debug("Neo4j connectivity check failed.", exc_info=True)
            return False

    def close(self) -> None:
        self._manager.close()

    def sync_user_interaction(self, user_id: str, media_title: str, interaction_type: str) -> None:
        """Synchronise l'interaction de l'utilisateur dans le graphe (User -> Media)."""
        query = """
        MERGE (u:User {id: $user_id})
        MERGE (m:Media {title: $media_title})
        CREATE (u)-[:INTERACTED_WITH {type: $interaction_type, timestamp: timestamp()}]->(m)
        """
        try:
            self.execute_write(query, {"user_id": user_id, "media_title": media_title, "interaction_type": interaction_type})
            logger.info(f"📊 Graph User Memory: Logged interaction for user={user_id} with media={media_title}")
        except Exception as e:
            logger.warning(f"⚠️ Graph User Memory: Failed to sync interaction: {e}")

    def get_user_preferences_context(self, user_id: str) -> str:
        """Récupère l'historique et les préférences utilisateur pour enrichir le RAG."""
        query = """
        MATCH (u:User {id: $user_id})-[r:INTERACTED_WITH]->(m:Media)
        RETURN m.title as title, r.type as type, r.timestamp as ts
        ORDER BY r.timestamp DESC
        LIMIT 5
        """
        try:
            results = self.execute_read(query, {"user_id": user_id})
            if not results:
                return ""
            history_str = ", ".join([f"'{item['title']}' ({item['type']})" for item in results])
            return f"\n[Préférences Utilisateur RAG]: L'utilisateur '{user_id}' a récemment interagi avec : {history_str}.\n"
        except Exception as e:
            logger.warning(f"⚠️ Graph User Memory: Failed to retrieve preferences: {e}")
            return ""

    def get_neighborhood(self, item_id: str, media_type: str, depth: int = 1) -> Dict[str, Any]:
        """Retrieves nodes and relationships within a certain depth using APOC."""
        query = """
        MATCH (start:Media {id: $id, type: $type})
        CALL apoc.path.subgraphAll(start, {maxLevel: $depth})
        YIELD nodes, relationships
        RETURN [n in nodes | {id: id(n), properties: properties(n), labels: labels(n)}] as nodes,
               [r in relationships | {id: id(r), source: id(startNode(r)), target: id(endNode(r)), type: type(r), properties: properties(r)}] as links
        """
        try:
            results = self.execute_read(query, {"id": item_id, "type": media_type, "depth": depth})
            if not results:
                return {"nodes": [], "links": []}
            return results[0]
        except Exception as e:
            logger.error(f"❌ Neo4j Adapter: Failed to fetch neighborhood for {item_id}: {e}")
            return {"nodes": [], "links": []}

