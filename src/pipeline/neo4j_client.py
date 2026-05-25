import logging
from neo4j import GraphDatabase
import os
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

from core.ports.graph_database_port import GraphDatabasePort

logger = logging.getLogger("animetix.neo4j")

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "secretpassword")

class Neo4jManager(GraphDatabasePort):
    def __init__(self):
        self._driver = None
        self._uri = NEO4J_URI
        self._user = NEO4J_USER
        self._password = NEO4J_PASSWORD

    @property
    def driver(self):
        if self._driver is None:
            try:
                self._driver = GraphDatabase.driver(
                    self._uri, 
                    auth=(self._user, self._password),
                    connection_timeout=5.0,
                    max_transaction_retry_time=10.0
                )
                self._driver.verify_connectivity()
                # print(f"✅ Successfully connected to Neo4j at {self._uri}") # Removed print for clean logs
            except Exception as e:
                # logger.warning(f"⚠️ Neo4j Connection Failed: {e}")
                self._driver = None
        return self._driver

    def close(self):
        if self.driver:
            self.driver.close()

    def sync_media_to_graph(self, media_item, media_type):
        """Injecte une œuvre et ses relations de base dans le graphe."""
        if not self.driver: return
        with self.driver.session() as session:
            session.execute_write(self._sync_tx, media_item, media_type)

    def sync_ai_extracted_graph(self, media_id: str, extracted_data: dict):
        """Injecte les entités et relations extraites par l'IA dans le graphe."""
        if not self.driver or not extracted_data: return
        with self.driver.session() as session:
            # 1. Création des Entités
            for entity in extracted_data.get('entities', []):
                session.execute_write(self._create_entity_tx, entity)
            # 2. Création des Relations
            for rel in extracted_data.get('relations', []):
                session.execute_write(self._create_relation_tx, rel)
            # 3. Lier au média parent
            session.execute_write(self._link_to_parent_tx, media_id, extracted_data.get('entities', []))

    def sync_combat_lore(self, media_id: str, lore_data_list: List[Dict[str, Any]]):
        """Injects extracted combat lore into the graph."""
        if not self.driver or not lore_data_list:
            return
            
        with self.driver.session() as session:
            for lore in lore_data_list:
                try:
                    session.execute_write(self._sync_combat_tx, str(media_id), lore)
                except Exception as e:
                    logger.error(f"Failed to sync combat lore for {lore.get('technique', 'unknown')}: {e}")

    @staticmethod
    def _sync_combat_tx(tx, media_id: str, lore: Dict[str, Any]):
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
        tx.run(query, 
            media_id=media_id,
            character=lore.get('character'),
            technique=lore.get('technique'),
            timestamp=lore.get('timestamp'),
            description=lore.get('visual_description')
        )

    @staticmethod
    def _create_entity_tx(tx, entity):
        query = "MERGE (e:Entity {name: $name}) SET e.type = $type, e.description = $description RETURN e"
        tx.run(query, name=entity['name'], type=entity['type'], description=entity.get('description', ''))

    @staticmethod
    def _create_relation_tx(tx, rel):
        query = "MATCH (a:Entity {name: $source}) MATCH (b:Entity {name: $target}) MERGE (a)-[r:AI_RELATION {type: $rel_type}]->(b) RETURN r"
        tx.run(query, source=rel['source'], target=rel['target'], rel_type=rel['type'])

    @staticmethod
    def _link_to_parent_tx(tx, media_id, entities):
        for ent in entities:
            query = "MATCH (m:Media {id: $m_id}) MATCH (e:Entity {name: $e_name}) MERGE (m)-[:FEATURES]->(e)"
            tx.run(query, m_id=str(media_id), e_name=ent['name'])

    @staticmethod
    def _sync_tx(tx, item, media_type):
        query = "MERGE (m:Media {id: $id, type: $type}) SET m.title = $title, m.year = $year RETURN m"
        tx.run(query, id=str(item['id']), type=media_type, title=item['title'], year=item.get('year'))
        for studio_name in item.get('studios', []):
            tx.run("MATCH (m:Media {id: $id}) MERGE (s:Studio {name: $studio_name}) MERGE (m)-[:PRODUCED_BY]->(s)", id=str(item['id']), studio_name=studio_name)
        for tag in item.get('micro_tags', []):
            tx.run("MATCH (m:Media {id: $id}) MERGE (t:MicroTag {name: $tag_name}) MERGE (m)-[:HAS_THEME]->(t)", id=str(item['id']), tag_name=tag)
        author = item.get('graph_nodes', {}).get('author') or item.get('graph_nodes', {}).get('director')
        if author:
            tx.run("MATCH (m:Media {id: $id}) MERGE (p:Person {name: $author_name}) MERGE (m)-[:CREATED_BY]->(p)", id=str(item['id']), author_name=author)

    def sync_saga(self, saga_name: str, executive_summary: str, media_ids: List[str]):
        """
        Creates a Saga node and links it to its media items.
        """
        if not self.driver:
            return
            
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
                session.run(query, saga_name=saga_name, summary=executive_summary, ids=media_ids)
            except Exception as e:
                logger.error(f"Failed to sync saga {saga_name}: {e}")

    def sync_fan_theory(self, saga_name: str, theory_data: Dict[str, Any]):
        """
        Creates a FanTheory node and links it to the Saga.
        theory_data: {
            'title': str,
            'description': str,
            'popularity': str (High/Med/Low),
            'plausibility': float (0-1),
            'source_url': str
        }
        """
        if not self.driver:
            return
        with self.driver.session() as session:
            try:
                session.execute_write(self._sync_fan_theory_tx, saga_name, theory_data)
            except Exception as e:
                logger.error(f"Failed to sync fan theory {theory_data.get('title')} for {saga_name}: {e}")

    @staticmethod
    def _sync_fan_theory_tx(tx, saga_name: str, theory_data: Dict[str, Any]):
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
            saga_name=saga_name,
            title=theory_data.get('title'),
            description=theory_data.get('description'),
            popularity=theory_data.get('popularity'),
            plausibility=theory_data.get('plausibility'),
            source_url=theory_data.get('source_url', '')
        )

    def find_logical_connections(self, media_id):
        if not self.driver: return []
        query = "MATCH (m:Media {id: $id})-[:PRODUCED_BY|CREATED_BY|HAS_THEME*1..2]-(related:Media) WHERE m <> related RETURN related.title AS title, count(*) AS strength ORDER BY strength DESC LIMIT 5"
        with self.driver.session() as session:
            result = session.run(query, id=str(media_id))
            return [record.data() for record in result]

    # --- ADVANCED GRAPHRAG (2026 SOTA) ---

    def get_community_summary(self, category_type: str, category_name: str) -> str:
        """
        Global Summarization : Récupère une vue d'ensemble d'une 'communauté' (ex: un genre, un studio).
        """
        if not self.driver: return ""
        
        # On agrège les thèmes, les studios et les créateurs dominants de la communauté
        query = f"""
        MATCH (cat:{category_type} {{name: $name}})<-[:PRODUCED_BY|HAS_THEME|CREATED_BY*1..2]-(m:Media)
        OPTIONAL MATCH (m)-[:HAS_THEME]->(t:MicroTag)
        OPTIONAL MATCH (m)-[:PRODUCED_BY]->(s:Studio)
        RETURN count(DISTINCT m) as total_works,
               collect(DISTINCT t.name)[0..10] as top_themes,
               collect(DISTINCT s.name)[0..5] as key_studios
        """
        with self.driver.session() as session:
            res = session.run(query, name=category_name).single()
            if not res or res['total_works'] == 0:
                return f"Aucune donnée globale trouvée pour la communauté {category_name}."
            
            return f"COMMUNAUTÉ {category_name} ({category_type}) :\n" \
                   f"- Volume : {res['total_works']} œuvres liées.\n" \
                   f"- Thèmes récurrents : {', '.join(res['top_themes'])}\n" \
                   f"- Acteurs majeurs : {', '.join(res['key_studios'])}"

    def multi_hop_traversal(self, start_node: str, steps: List[str]) -> str:
        """
        Graph Traversal Reasoning : Navigue explicitement sur un chemin défini par l'IA.
        Ex: steps=['CREATED_BY', 'CREATED_BY', 'PRODUCED_BY'] -> Suivre Créateur puis ses autres œuvres.
        """
        if not self.driver or not steps: return ""
        
        # Construction dynamique du chemin Cypher
        rel_chain = "-[:" + "]-() -[:".join(steps) + "]-"
        query = f"""
        MATCH (start {{name: $name}}){rel_chain}(target)
        RETURN DISTINCT target.name as name, labels(target)[0] as type
        LIMIT 10
        """
        
        logger.info(f"🕸️ Multi-Hop: Traversing path {steps} from {start_node}")
        
        context = []
        with self.driver.session() as session:
            result = session.run(query, name=start_node)
            for record in result:
                context.append(f"{record['type']}: {record['name']}")
        
        if not context:
            return f"Le chemin {steps} n'a mené à aucun résultat depuis {start_node}."
            
        return f"RÉSULTATS DU CHEMIN ({' -> '.join(steps)}) :\n" + "\n".join(context)

    def get_studio_trends(self, studio_name: str, years_back: int = 3) -> str:
        """Analyse les tendances récentes d'un studio."""
        if not self.driver: return ""
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
            if not themes: return f"Pas de tendances récentes trouvées pour {studio_name}."
            return f"Tendances {studio_name} (dernières années) : {', '.join(themes)}."

    def get_creator_network_context(self, person_name: str):
        if not self.driver: return ""
        query = "MATCH (p:Person {name: $name})<-[:CREATED_BY]-(m:Media)-[:PRODUCED_BY]->(s:Studio) WITH s, count(m) AS collab_count RETURN s.name AS studio, collab_count ORDER BY collab_count DESC LIMIT 5"
        with self.driver.session() as session:
            result = session.run(query, name=person_name)
            collabs = [f"{r['studio']} ({r['collab_count']} œuvres)" for r in result]
            if not collabs: return f"Pas de données de réseau pour {person_name}."
            return f"Réseau de {person_name} : Collaborations principales avec {', '.join(collabs)}."

    def get_enriched_context(self, media_ids: list):
        if not self.driver or not media_ids: return ""
        query = "MATCH (m:Media) WHERE m.id IN $ids OPTIONAL MATCH (m)-[:PRODUCED_BY]->(s:Studio) OPTIONAL MATCH (m)-[:CREATED_BY]->(p:Person) OPTIONAL MATCH (m)-[:HAS_THEME]->(t:MicroTag) RETURN m.title AS title, collect(DISTINCT s.name) AS studios, collect(DISTINCT p.name) AS creators, collect(DISTINCT t.name) AS themes"
        context_parts = []
        with self.driver.session() as session:
            result = session.run(query, ids=[str(i) for i in media_ids])
            for record in result:
                part = f"Oeuvre: {record['title']}"
                if record['studios']: part += f" | Studios: {', '.join(record['studios'])}"
                if record['creators']: part += f" | Créateurs: {', '.join(record['creators'])}"
                if record['themes']: part += f" | Thèmes: {', '.join(record['themes'])}"
                context_parts.append(part)
        return "\n".join(context_parts)

    def verify_claims(self, claims: List[Dict]) -> List[Dict]:
        """
        Vérifie une liste de faits (claims) par rapport au graphe Neo4j.
        Ex: { "subject": "Naruto", "relation": "STUDIO", "object": "Pierrot" }
        """
        results = []
        with self.driver.session() as session:
            for claim in claims:
                subj = claim.get('subject')
                rel = claim.get('relation', '').upper()
                obj = claim.get('object')
                
                # Requête générique pour vérifier un lien
                query = f"""
                MATCH (s:Media {{title: $subj}})-[:{rel}]->(o {{name: $obj}})
                RETURN count(o) > 0 as verified
                """
                if rel == "PRODUCED_BY": # Cas spécifique Studio
                     query = """
                     MATCH (s:Media {title: $subj})-[:PRODUCED_BY]->(o:Studio {name: $obj})
                     RETURN count(o) > 0 as verified
                     """
                
                res = session.run(query, {"subj": subj, "obj": obj}).single()
                verified = res['verified'] if res else False
                results.append({**claim, "verified": verified})
        return results

    def execute_query(self, query: str, parameters: Optional[Dict] = None) -> List[Dict]:
        """Exécute une requête Cypher brute de manière sécurisée."""
        if not self.driver: return []
        with self.driver.session() as session:
            try:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
            except Exception as e:
                logger.error(f"Cypher Execution Error: {e}\nQuery: {query}")
                return []

neo4j_manager = Neo4jManager()
