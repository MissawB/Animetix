from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "secretpassword")

class Neo4jManager:
    def __init__(self):
        try:
            # On définit des paramètres de connexion plus courts pour éviter les hangs infinis en local
            self.driver = GraphDatabase.driver(
                NEO4J_URI, 
                auth=(NEO4J_USER, NEO4J_PASSWORD),
                connection_timeout=5.0,  # 5 secondes max pour établir la connexion
                max_transaction_retry_time=10.0 # 10 secondes max pour les retries de transactions
            )
            # Vérification réelle de la connectivité
            self.driver.verify_connectivity()
            print(f"✅ Successfully connected to Neo4j at {NEO4J_URI}")
        except Exception as e:
            print(f"⚠️ Neo4j Connection Failed: {e}")
            print("ℹ️ Graph synchronization will be skipped.")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def sync_media_to_graph(self, media_item, media_type):
        """Injecte une œuvre et ses relations dans le graphe."""
        if not self.driver: return

        with self.driver.session() as session:
            session.execute_write(self._sync_tx, media_item, media_type)

    @staticmethod
    def _sync_tx(tx, item, media_type):
        # 1. Créer le nœud principal
        query = (
            "MERGE (m:Media {id: $id, type: $type}) "
            "SET m.title = $title, m.year = $year "
            "RETURN m"
        )
        tx.run(query, id=str(item['id']), type=media_type, title=item['title'], year=item.get('year'))

        # 2. Gérer les Studios (Relation: PRODUCED_BY)
        for studio_name in item.get('studios', []):
            tx.run(
                "MATCH (m:Media {id: $id}) "
                "MERGE (s:Studio {name: $studio_name}) "
                "MERGE (m)-[:PRODUCED_BY]->(s)",
                id=str(item['id']), studio_name=studio_name
            )

        # 3. Gérer les Micro-Tags (Relation: HAS_THEME)
        for tag in item.get('micro_tags', []):
            tx.run(
                "MATCH (m:Media {id: $id}) "
                "MERGE (t:MicroTag {name: $tag_name}) "
                "MERGE (m)-[:HAS_THEME]->(t)",
                id=str(item['id']), tag_name=tag
            )
            
        # 4. Gérer l'Auteur/Réalisateur (Relation: CREATED_BY)
        author = item.get('graph_nodes', {}).get('author') or item.get('graph_nodes', {}).get('director')
        if author:
            tx.run(
                "MATCH (m:Media {id: $id}) "
                "MERGE (p:Person {name: $author_name}) "
                "MERGE (m)-[:CREATED_BY]->(p)",
                id=str(item['id']), author_name=author
            )

    def find_logical_connections(self, media_id):
        """Trouve les connexions complexes via le graphe."""
        if not self.driver: return []
        
        query = (
            "MATCH (m:Media {id: $id})-[:PRODUCED_BY|CREATED_BY|HAS_THEME*1..2]-(related:Media) "
            "WHERE m <> related "
            "RETURN related.title AS title, count(*) AS strength "
            "ORDER BY strength DESC LIMIT 5"
        )
        with self.driver.session() as session:
            result = session.run(query, id=str(media_id))
            return [record.data() for record in result]

    def get_enriched_context(self, media_ids: list):
        """Récupère un contexte textuel enrichi pour une liste d'IDs (Studios, Thèmes, Créateurs)."""
        if not self.driver or not media_ids: return ""
        
        query = (
            "MATCH (m:Media) WHERE m.id IN $ids "
            "OPTIONAL MATCH (m)-[:PRODUCED_BY]->(s:Studio) "
            "OPTIONAL MATCH (m)-[:CREATED_BY]->(p:Person) "
            "OPTIONAL MATCH (m)-[:HAS_THEME]->(t:MicroTag) "
            "RETURN m.title AS title, "
            "collect(DISTINCT s.name) AS studios, "
            "collect(DISTINCT p.name) AS creators, "
            "collect(DISTINCT t.name) AS themes"
        )
        
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

neo4j_manager = Neo4jManager()
