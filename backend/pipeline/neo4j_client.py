import logging
import re
from neo4j import GraphDatabase
import os
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

from core.ports.graph_database_port import GraphDatabasePort
from core.utils.security import sanitize_cypher_identifier, sanitize_for_prompt

logger = logging.getLogger("animetix." + __name__)

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

ALLOWED_LABELS = {
    "Media",
    "Studio",
    "Person",
    "MicroTag",
    "Character",
    "CombatEvent",
    "Saga",
    "FanTheory",
    "Entity",
    "User",
    "Technique",
}

ALLOWED_RELATIONSHIPS = {
    "PRODUCED_BY",
    "HAS_THEME",
    "CREATED_BY",
    "FEATURES",
    "VOICED_BY",
    "DIRECTED_BY",
    "CONTAINS_COMBAT",
    "PERFORMS",
    "INVOLVES_TECHNIQUE",
    "USES_TECHNIQUE",
    "CONTAINS_MEDIA",
    "HAS_THEORY",
    "INTERACTED_WITH",
    "APPEARS_IN",
    "AI_RELATION",
}


class Neo4jManager(GraphDatabasePort):
    def __init__(self, uri=None, user=None, password=None):
        self._driver = None
        self._uri = uri or NEO4J_URI
        self._user = user or NEO4J_USER
        self._password = password or NEO4J_PASSWORD

    @property
    def driver(self):
        if self._driver is None:
            try:
                self._driver = GraphDatabase.driver(
                    self._uri,
                    auth=(self._user, self._password),
                    connection_timeout=5.0,
                    max_transaction_retry_time=10.0,
                )
                self._driver.verify_connectivity()
                logger.info(f"✅ Successfully connected to Neo4j at {self._uri}")
            except Exception as e:
                logger.warning(f"⚠️ Neo4j Connection Failed: {e}")
                self._driver = None
        return self._driver

    def close(self):
        if self.driver:
            self.driver.close()

    def sync_media_to_graph(self, media_item, media_type):
        """Injecte une œuvre et ses relations de base dans le graphe."""
        if not self.driver:
            return
        with self.driver.session() as session:
            session.execute_write(self._sync_tx, media_item, media_type)

    def sync_character_to_graph(self, character_item: dict):
        """Injects a Character node and links it to associated media."""
        if not self.driver:
            return
        with self.driver.session() as session:
            session.execute_write(self._sync_character_tx, character_item)

    @staticmethod
    def _sync_character_tx(tx, item):
        # Sanitization before graph injection
        clean_item = sanitize_for_prompt(item)
        query = "MERGE (c:Character {id: $id}) SET c.name = $name RETURN c"
        tx.run(query, id=str(clean_item["id"]), name=clean_item.get("name"))

        # Link to anime or manga if present in the data
        for anime_id in clean_item.get("anime_appearances", []):
            tx.run(
                "MATCH (c:Character {id: $cid}) MATCH (m:Media {id: $mid}) MERGE (c)-[:APPEARS_IN]->(m)",
                cid=str(clean_item["id"]),
                mid=str(anime_id),
            )

    def sync_ai_extracted_graph(self, media_id: str, extracted_data: dict):
        """Injecte les entités et relations extraites par l'IA dans le graphe."""
        if not self.driver or not extracted_data:
            return
        # Recursive sanitization of extracted data (LLM-generated)
        clean_data = sanitize_for_prompt(extracted_data)
        with self.driver.session() as session:
            for entity in clean_data.get("entities", []):
                session.execute_write(self._create_entity_tx, entity)
            for rel in clean_data.get("relations", []):
                session.execute_write(self._create_relation_tx, rel)
            session.execute_write(
                self._link_to_parent_tx, media_id, clean_data.get("entities", [])
            )

    def sync_combat_lore(self, media_id: str, lore_data_list: List[Dict[str, Any]]):
        """Injects extracted combat lore into the graph."""
        if not self.driver or not lore_data_list:
            return

        with self.driver.session() as session:
            for lore in lore_data_list:
                try:
                    session.execute_write(self._sync_combat_tx, str(media_id), lore)
                except Exception as e:
                    logger.error(f"Failed to sync combat lore: {e}")

    @staticmethod
    def _sync_combat_tx(tx, media_id: str, lore: Dict[str, Any]):
        clean_lore = sanitize_for_prompt(lore)
        query = """
        MATCH (m:Media {id: $media_id})
        MERGE (c:Character {name: $character})
        MERGE (t:Technique {name: $technique})
        CREATE (e:CombatEvent {
            timestamp: $timestamp, 
            description: $description,
            created_at: datetime()
        })
        MERGE (m)-[:CONTAINS_COMBAT]->(e)
        MERGE (c)-[:PERFORMS]->(e)
        MERGE (e)-[:INVOLVES_TECHNIQUE]->(t)
        MERGE (c)-[:USES_TECHNIQUE]->(t)
        """
        tx.run(
            query,
            media_id=media_id,
            character=clean_lore.get("character"),
            technique=clean_lore.get("technique"),
            timestamp=clean_lore.get("timestamp"),
            description=clean_lore.get("visual_description"),
        )

    @staticmethod
    def _create_entity_tx(tx, entity):
        clean_ent = sanitize_for_prompt(entity)
        query = "MERGE (e:Entity {name: $name}) SET e.type = $type, e.description = $description RETURN e"
        tx.run(
            query,
            name=clean_ent["name"],
            type=clean_ent["type"],
            description=clean_ent.get("description", ""),
        )

    @staticmethod
    def _create_relation_tx(tx, rel):
        clean_rel = sanitize_for_prompt(rel)
        rel_type_raw = clean_rel["type"]
        try:
            safe_type = sanitize_cypher_identifier(
                rel_type_raw.upper(), ALLOWED_RELATIONSHIPS
            )
            query = f"MATCH (a:Entity {{name: $source}}) MATCH (b:Entity {{name: $target}}) MERGE (a)-[r:{safe_type}]->(b) RETURN r"
            tx.run(query, source=clean_rel["source"], target=clean_rel["target"])
        except ValueError:
            query = "MATCH (a:Entity {name: $source}) MATCH (b:Entity {name: $target}) MERGE (a)-[r:AI_RELATION {type: $rel_type}]->(b) RETURN r"
            tx.run(
                query,
                source=clean_rel["source"],
                target=clean_rel["target"],
                rel_type=rel_type_raw,
            )

    @staticmethod
    def _link_to_parent_tx(tx, media_id, entities):
        for ent in entities:
            clean_ent = sanitize_for_prompt(ent)
            query = "MATCH (m:Media {id: $m_id}) MATCH (e:Entity {name: $e_name}) MERGE (m)-[:FEATURES]->(e)"
            tx.run(query, m_id=str(media_id), e_name=clean_ent["name"])

    @staticmethod
    def _sync_tx(tx, item, media_type):
        clean_item = sanitize_for_prompt(item)
        safe_media_label = "Media"
        query = f"MERGE (m:{safe_media_label} {{id: $id, type: $type}}) SET m.title = $title, m.year = $year RETURN m"
        tx.run(
            query,
            id=str(clean_item["id"]),
            type=media_type,
            title=clean_item["title"],
            year=clean_item.get("year"),
        )
        for studio_name in clean_item.get("studios", []):
            tx.run(
                "MATCH (m:Media {id: $id}) MERGE (s:Studio {name: $studio_name}) MERGE (m)-[:PRODUCED_BY]->(s)",
                id=str(clean_item["id"]),
                studio_name=studio_name,
            )
        for tag in clean_item.get("micro_tags", []):
            tx.run(
                "MATCH (m:Media {id: $id}) MERGE (t:MicroTag {name: $tag_name}) MERGE (m)-[:HAS_THEME]->(t)",
                id=str(clean_item["id"]),
                tag_name=tag,
            )
        author = clean_item.get("graph_nodes", {}).get("author") or clean_item.get(
            "graph_nodes", {}
        ).get("director")
        if author:
            tx.run(
                "MATCH (m:Media {id: $id}) MERGE (p:Person {name: $author_name}) MERGE (m)-[:CREATED_BY]->(p)",
                id=str(clean_item["id"]),
                author_name=author,
            )

    def sync_saga(self, saga_name: str, executive_summary: str, media_ids: List[str]):
        if not self.driver:
            return
        clean_saga = sanitize_for_prompt(saga_name)
        clean_summary = sanitize_for_prompt(executive_summary)
        query = """
        MERGE (s:Saga {name: $saga_name})
        SET s.executive_summary = $summary, s.updated_at = datetime()
        WITH s
        UNWIND $ids as mid
        MATCH (m:Media {id: mid})
        MERGE (s)-[:CONTAINS_MEDIA]->(m)
        """
        with self.driver.session() as session:
            try:
                session.run(
                    query, saga_name=clean_saga, summary=clean_summary, ids=media_ids
                )
            except Exception as e:
                logger.error(f"Failed to sync saga {saga_name}: {e}")

    def sync_fan_theory(self, saga_name: str, theory_data: Dict[str, Any]):
        if not self.driver:
            return
        with self.driver.session() as session:
            try:
                session.execute_write(self._sync_fan_theory_tx, saga_name, theory_data)
            except Exception as e:
                logger.error(f"Failed to sync fan theory: {e}")

    @staticmethod
    def _sync_fan_theory_tx(tx, saga_name: str, theory_data: Dict[str, Any]):
        clean_theory = sanitize_for_prompt(theory_data)
        clean_saga = sanitize_for_prompt(saga_name)
        query = """
        MERGE (s:Saga {name: $saga_name})
        MERGE (t:FanTheory {title: $title})
        SET t.description = $description,
            t.popularity = $popularity,
            t.plausibility = $plausibility,
            t.source_url = $source_url,
            t.updated_at = datetime()
        MERGE (s)-[:HAS_THEORY]->(t)
        """
        tx.run(
            query,
            saga_name=clean_saga,
            title=clean_theory.get("title"),
            description=clean_theory.get("description"),
            popularity=clean_theory.get("popularity"),
            plausibility=clean_theory.get("plausibility"),
            source_url=clean_theory.get("source_url", ""),
        )

    def find_logical_connections(self, media_id):
        if not self.driver:
            return []
        query = "MATCH (m:Media {id: $id})-[:PRODUCED_BY|CREATED_BY|HAS_THEME*1..2]-(related:Media) WHERE m <> related RETURN related.title AS title, count(*) AS strength ORDER BY strength DESC LIMIT 5"
        with self.driver.session() as session:
            result = session.run(query, id=str(media_id))
            return [record.data() for record in result]

    def get_community_summary(self, category_type: str, category_name: str) -> str:
        if not self.driver:
            return ""
        safe_label = sanitize_cypher_identifier(category_type, ALLOWED_LABELS)
        query = f"""
        MATCH (cat:{safe_label} {{name: $name}})<-[:PRODUCED_BY|HAS_THEME|CREATED_BY*1..2]-(m:Media)
        OPTIONAL MATCH (m)-[:HAS_THEME]->(t:MicroTag)
        OPTIONAL MATCH (m)-[:PRODUCED_BY]->(s:Studio)
        RETURN count(DISTINCT m) as total_works,
               collect(DISTINCT t.name)[0..10] as top_themes,
               collect(DISTINCT s.name)[0..5] as key_studios
        """
        with self.driver.session() as session:
            res = session.run(query, name=category_name).single()
            if not res or res["total_works"] == 0:
                return (
                    f"Aucune donnée globale trouvée pour la communauté {category_name}."
                )

            return (
                f"COMMUNAUTÉ {category_name} ({category_type}) :\n"
                f"- Volume : {res['total_works']} œuvres liées.\n"
                f"- Thèmes récurrents : {', '.join(res['top_themes'])}\n"
                f"- Acteurs majeurs : {', '.join(res['key_studios'])}"
            )

    def multi_hop_traversal(self, start_node: str, steps: List[str]) -> str:
        if not self.driver or not steps:
            return ""
        safe_steps = [
            sanitize_cypher_identifier(s, ALLOWED_RELATIONSHIPS) for s in steps
        ]
        rel_chain = "-[:" + "]-() -[:".join(safe_steps) + "]-"
        query = f"""
        MATCH (start {{name: $name}}){rel_chain}(target)
        RETURN DISTINCT target.name as name, labels(target)[0] as type
        LIMIT 10
        """
        context = []
        with self.driver.session() as session:
            result = session.run(query, name=start_node)
            for record in result:
                context.append(f"{record['type']}: {record['name']}")

        if not context:
            return f"Le chemin {steps} n'a mené à aucun résultat depuis {start_node}."

        return f"RÉSULTATS DU CHEMIN ({' -> '.join(steps)}) :\n" + "\n".join(context)

    def get_studio_trends(self, studio_name: str, years_back: int = 3) -> str:
        if not self.driver:
            return ""
        query = """
        MATCH (s:Studio {name: $name})<-[:PRODUCED_BY]-(m:Media)
        WHERE m.year >= (date().year - $years)
        MATCH (m)-[:HAS_THEME]->(t:MicroTag)
        RETURN t.name as theme, count(m) as weight
        ORDER BY weight DESC LIMIT 5
        """
        with self.driver.session() as session:
            result = session.run(query, name=studio_name, years=years_back)
            themes = [f"{r['theme']} ({r['weight']})" for r in result]
            if not themes:
                return f"Pas de tendances récentes trouvées pour {studio_name}."
            return f"Tendances {studio_name} (dernières années) : {', '.join(themes)}."

    def get_creator_network_context(self, person_name: str):
        if not self.driver:
            return ""
        query = "MATCH (p:Person {name: $name})<-[:CREATED_BY]-(m:Media)-[:PRODUCED_BY]->(s:Studio) WITH s, count(m) AS collab_count RETURN s.name AS studio, collab_count ORDER BY collab_count DESC LIMIT 5"
        with self.driver.session() as session:
            result = session.run(query, name=person_name)
            collabs = [f"{r['studio']} ({r['collab_count']} œuvres)" for r in result]
            if not collabs:
                return f"Pas de données de réseau pour {person_name}."
            return f"Réseau de {person_name} : Collaborations principales avec {', '.join(collabs)}."

    def get_enriched_context(self, media_ids: list):
        if not self.driver or not media_ids:
            return ""
        query = "MATCH (m:Media) WHERE m.id IN $ids OPTIONAL MATCH (m)-[:PRODUCED_BY]->(s:Studio) OPTIONAL MATCH (m)-[:CREATED_BY]->(p:Person) OPTIONAL MATCH (m)-[:HAS_THEME]->(t:MicroTag) RETURN m.title AS title, collect(DISTINCT s.name) AS studios, collect(DISTINCT p.name) AS creators, collect(DISTINCT t.name) AS themes"
        context_parts = []
        with self.driver.session() as session:
            result = session.run(query, ids=[str(i) for i in media_ids])
            for record in result:
                part = f"Oeuvre: {record['title']}"
                if record["studios"]:
                    part += f" | Studios: {', '.join(record['studios'])}"
                if record["creators"]:
                    part += f" | Créateurs: {', '.join(record['creators'])}"
                if record["themes"]:
                    part += f" | Thèmes: {', '.join(record['themes'])}"
                context_parts.append(part)
        return "\n".join(context_parts)

    def verify_claims(self, claims: List[Dict]) -> List[Dict]:
        results = []
        with self.driver.session() as session:
            for claim in claims:
                subj = claim.get("subject")
                rel_raw = claim.get("relation", "").upper()
                obj = claim.get("object")
                try:
                    safe_rel = sanitize_cypher_identifier(
                        rel_raw, ALLOWED_RELATIONSHIPS
                    )
                    query = f"MATCH (s:Media {{title: $subj}})-[:{safe_rel}]->(o {{name: $obj}}) RETURN count(o) > 0 as verified"
                    res = session.run(query, {"subj": subj, "obj": obj}).single()
                    verified = res["verified"] if res else False
                    results.append({**claim, "verified": verified})
                except ValueError:
                    results.append(
                        {
                            **claim,
                            "verified": False,
                            "error": "Unauthorized relation type",
                        }
                    )
        return results

    @staticmethod
    def is_safe_read_query(query: str) -> bool:
        dangerous_keywords = {
            "DELETE",
            "DETACH",
            "DROP",
            "CREATE",
            "MERGE",
            "SET",
            "REMOVE",
            "CALL",
            "LOAD",
            "CSV",
            "PERIODIC",
            "COMMIT",
        }
        query_upper = query.upper()
        for kw in dangerous_keywords:
            if re.search(rf"\b{kw}\b", query_upper):
                logger.error(
                    f"❌ Security Alert: Dangerous Cypher keyword '{kw}' detected."
                )
                return False
        return True

    def execute_read(self, query: str, parameters: Optional[Dict] = None) -> List[Dict]:
        if not self.is_safe_read_query(query):
            raise ValueError("Dangerous Cypher query rejected.")
        if not self.driver:
            return []
        with self.driver.session() as session:
            try:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
            except Exception as e:
                logger.error(f"Cypher Error (Read): {e}")
                return []

    def execute_query(
        self, query: str, parameters: Optional[Dict] = None
    ) -> List[Dict]:
        if not self.driver:
            return []
        with self.driver.session() as session:
            try:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
            except Exception as e:
                logger.error(f"Cypher Error: {e}")
                return []


neo4j_manager = Neo4jManager()
