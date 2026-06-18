import logging
from typing import List, Dict, Any
from ...ports.inference_port import InferencePort

logger = logging.getLogger("animetix.graph.healer")


class GraphHealerService:
    """
    Service de domaine gérant l'auto-guérison et la construction résiliente du Knowledge Graph.
    Il surveille les lacunes dans Neo4j et déclenche des extractions IA si nécessaire.
    """

    def __init__(
        self,
        neo4j_manager,
        construction_service,
        repository,
        inference_engine: InferencePort,
    ):
        self.neo4j = neo4j_manager
        self.construction_service = construction_service
        self.repository = repository
        self.inference_engine = inference_engine

    def ensure_graph_integrity(self, media_ids: List[str]):
        """
        Vérifie si les nœuds et relations pour ces IDs existent dans Neo4j.
        Sinon, déclenche une reconstruction partielle.
        """
        if not self.neo4j or not self.neo4j.driver:
            logger.warning("⚠️ Self-Healing skipped: Neo4j not available.")
            return

        missing_ids = self._identify_missing_nodes(media_ids)
        if not missing_ids:
            return

        logger.info(
            f"🕸️ Self-Healing: {len(missing_ids)} nodes missing in KG. Healing starts..."
        )
        for mid in missing_ids:
            try:
                self.heal_node(mid)
            except Exception as e:
                logger.error(f"❌ Failed to heal node {mid}: {e}")

    def heal_node(self, media_id: str):
        """Reconstruit un nœud spécifique et ses relations via extraction IA."""
        # 1. Get source of truth from SQL/Chroma
        media_data = self.repository.get_media_by_id(media_id)
        if not media_data:
            logger.error(f"Cannot heal {media_id}: No data found in repository.")
            return

        # 2. Extract base relations (Sync from metadata)
        self.neo4j.sync_media_to_graph(
            media_data, media_data.get("media_type", "Anime")
        )

        # 3. Extract complex relations via IA (if description is long enough)
        if len(media_data.get("description", "")) > 50:
            extracted = self.construction_service.extract_entities_and_relations(
                title=media_data["title"],
                description=media_data["description"],
                media_type=media_data.get("media_type", "Anime"),
            )
            self.neo4j.sync_ai_extracted_graph(media_id, extracted)
            logger.info(f"✅ Healed {media_id} with IA extraction.")

    def _identify_missing_nodes(self, media_ids: List[str]) -> List[str]:
        """Retourne les IDs qui n'existent pas dans Neo4j."""
        query = "MATCH (m:Media) WHERE m.id IN $ids RETURN m.id as id"
        existing = self.neo4j.execute_query(query, {"ids": [str(i) for i in media_ids]})
        existing_ids = {r["id"] for r in existing}
        return [mid for mid in media_ids if str(mid) not in existing_ids]

    def audit_graph_quality(self) -> Dict[str, Any]:
        """Effectue un diagnostic complet de l'état du Knowledge Graph."""
        if not self.neo4j or not self.neo4j.driver:
            return {"status": "error", "message": "Neo4j unavailable"}

        # 1. Compte des nœuds isolés
        query_isolated = "MATCH (n) WHERE NOT (n)--() RETURN count(n) as count"
        isolated_count = self.neo4j.execute_query(query_isolated)[0]["count"]

        # 2. Détection de conflits temporels (ex: suite sortie avant l'original)
        query_time_conflict = """
        MATCH (m1:Media)-[r:AI_RELATION {type: 'SEQUEL_OF'}]->(m2:Media)
        WHERE m1.year < m2.year
        RETURN m1.title as t1, m1.year as y1, m2.title as t2, m2.year as y2
        """
        conflicts = self.neo4j.execute_query(query_time_conflict)

        # 3. Nœuds sans lien avec une œuvre (Entities orphelines)
        query_orphans = "MATCH (e:Entity) WHERE NOT (e)<-[:FEATURES]-(:Media) RETURN count(e) as count"
        orphan_entities = self.neo4j.execute_query(query_orphans)[0]["count"]

        return {
            "status": "success",
            "isolated_nodes": isolated_count,
            "temporal_conflicts": len(conflicts),
            "orphan_entities": orphan_entities,
            "details": conflicts[:5],
        }

    def check_and_fix_broken_relations(self):
        """Identifie les nœuds isolés ou mal typés et tente de les réparer ou de les supprimer."""
        if not self.neo4j or not self.neo4j.driver:
            return

        logger.info("🧹 Starting Graph Cleanup cycle...")

        # 1. Supprimer les entités IA orphelines (bruit d'extraction)
        prune_query = "MATCH (e:Entity) WHERE NOT (e)<-[:FEATURES]-(:Media) DELETE e"
        self.neo4j.execute_query(prune_query)
        logger.info("✅ Orphan entities pruned.")

        # 2. Supprimer les relations temporelles incohérentes
        fix_time_query = """
        MATCH (m1:Media)-[r:AI_RELATION {type: 'SEQUEL_OF'}]->(m2:Media)
        WHERE m1.year < m2.year
        DELETE r
        """
        self.neo4j.execute_query(fix_time_query)
        logger.info("✅ Temporal contradictions resolved.")

        # 3. Réparer les nœuds Media sans relations de base (re-sync)
        query_no_base = "MATCH (m:Media) WHERE NOT (m)-[:PRODUCED_BY|HAS_THEME]->() RETURN m.id as id LIMIT 20"
        to_resync = self.neo4j.execute_query(query_no_base)

        for record in to_resync:
            self.heal_node(record["id"])

        logger.info(f"✅ Re-synced {len(to_resync)} incomplete media nodes.")
