import os
import sys
import json
import django
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(BASE_DIR, 'src', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')

def run_graph_healer(limit=100):
    """
    Agent IA autonome qui cherche des contradictions entre la base relationnelle (JSON/PG)
    et le graphe de connaissances (Neo4j).
    Crée des tickets de curation en cas de divergence.
    """
    if not django.apps.apps.ready:
        django.setup()
        
    from animetix.models import DataCurationTicket
    from pipeline.neo4j_client import neo4j_manager
    
    print("🩺 Starting Graph Healer Agent...")
    
    # 1. Charger la vérité terrain (PostgreSQL/JSON)
    db_path = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_animes.json')
    if not os.path.exists(db_path):
        print("❌ DB not found.")
        return
        
    with open(db_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Échantillonnage pour éviter de surcharger
    import random
    sample_data = random.sample(data, min(limit, len(data)))
    
    anomalies_found = 0
    
    for item in tqdm(sample_data, desc="Checking Graph Integrity"):
        title = item.get('title')
        pg_studios = set(item.get('studios', []))
        
        if not pg_studios:
            continue
            
        # 2. Interroger Neo4j
        query = """
        MATCH (m:Media {title: $title})-[:PRODUCED_BY]->(s:Studio)
        RETURN s.name as studio_name
        """
        neo4j_res = neo4j_manager.execute_query(query, {"title": title})
        neo4j_studios = set([r['studio_name'] for r in neo4j_res])
        
        # 3. Comparaison (Auto-Correction logic)
        # S'il y a une différence, on crée un ticket
        if pg_studios != neo4j_studios:
            issue_desc = f"Contradiction Studio détectée. PG: {pg_studios} vs Neo4j: {neo4j_studios}"
            
            # Vérifier si un ticket existe déjà
            ticket, created = DataCurationTicket.objects.get_or_create(
                item_title=title,
                is_resolved=False,
                defaults={
                    'issue_description': issue_desc,
                    'source_pg': {'studios': list(pg_studios)},
                    'source_neo4j': {'studios': list(neo4j_studios)}
                }
            )
            if created:
                anomalies_found += 1
                
    print(f"✅ Graph Healer finished. {anomalies_found} new curation tickets created.")

if __name__ == "__main__":
    run_graph_healer()
