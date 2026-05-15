import os
import sys
import django
import chromadb
from pathlib import Path

# Setup Project Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Since it's in Double_scenario_Project/scripts/reconcile_db.py
# parent is scripts, parent.parent is Double_scenario_Project
sys.path.append(str(PROJECT_ROOT / "src" / "backend"))
sys.path.append(str(PROJECT_ROOT / "src"))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')
django.setup()

from animetix.models import MediaItem
from pipeline.chroma_client import chroma_manager
from pipeline.neo4j_client import neo4j_manager

def reconcile():
    print("🔍 Starting Database Reconciliation...")
    
    # 1. Get Source of Truth (Django)
    items = MediaItem.objects.all()
    count = items.count()
    print(f"📊 Catalog Source: {count} items in Django.")

    if count == 0:
        print("⚠️ Django catalog is empty. Run 'python manage.py sync_catalog' first.")
        return

    # 2. Check ChromaDB
    collections = {
        'Anime': ['anime_thematic', 'anime_visual_vibe', 'anime_plot'],
        'Manga': ['manga_thematic', 'manga_visual_vibe'],
        'Character': ['character_vibe', 'character_visual_vibe'],
        'Movie': ['movie_thematic', 'movie_plot', 'movie_vibe'],
        'Game': ['game_thematic', 'game_plot', 'game_vibe'],
        'Actor': ['actor_vibe']
    }

    discrepancies = []
    
    # Sample check for performance (or full if count < 1000)
    check_items = items[:1000] if count > 1000 else items
    
    print(f"🕵️ Verifying {len(check_items)} sample items across DBs...")

    for item in check_items:
        issues = []
        
        # Chroma Check
        colls = collections.get(item.media_type, [])
        for coll_name in colls:
            try:
                coll = chroma_manager.get_collection(coll_name)
                res = coll.get(ids=[str(item.external_id)], include=[])
                if not res.get('ids'):
                    issues.append(f"Missing in Chroma:{coll_name}")
            except Exception as e:
                issues.append(f"Chroma Error:{coll_name}")

        # Neo4j Check (Simplified)
        try:
            # Assumes nodes have 'id' property and label matches media_type
            query = f"MATCH (n:{item.media_type} {{id: $id}}) RETURN n LIMIT 1"
            res = neo4j_manager.execute_query(query, {"id": item.external_id})
            if not res:
                issues.append("Missing in Neo4j")
        except:
            issues.append("Neo4j Check Failed")

        if issues:
            discrepancies.append({
                "item": str(item),
                "issues": issues
            })

    # 3. Report
    if not discrepancies:
        print("✅ SUCCESS: All sampled items are synchronized across Django, ChromaDB, and Neo4j.")
    else:
        print(f"❌ FOUND {len(discrepancies)} DISCREPANCIES:")
        for d in discrepancies[:20]: # Show first 20
            print(f"  - {d['item']}: {', '.join(d['issues'])}")
        
        if len(discrepancies) > 20:
            print(f"  ... and {len(discrepancies) - 20} more.")

if __name__ == "__main__":
    reconcile()
