import requests
import json
import os
from typing import List, Dict
from datetime import datetime

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_drift_detection(limit=20):
    """
    Vérifie si les animes les plus populaires de la saison actuelle sont présents dans le catalogue.
    Alerte si un 'drift' de connaissances est détecté.
    """
    print(f"🔍 Starting Knowledge Drift Detection ({datetime.now().date()})...")
    
    # 1. Récupérer les top animes de la saison via Jikan API
    try:
        res = requests.get("https://api.jikan.moe/v4/seasons/now", timeout=10)
        seasonal_animes = res.json().get('data', [])[:limit]
    except Exception as e:
        print(f"❌ Failed to fetch seasonal data: {e}")
        return {"status": "error", "message": str(e)}

    # 2. Charger le catalogue local (clean_root_animes.json)
    catalog_path = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_animes.json')
    if not os.path.exists(catalog_path):
        return {"status": "error", "message": "Catalog not found"}

    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
        existing_ids = {str(item['id']) for item in catalog}

    # 3. Comparaison
    missing = []
    for anime in seasonal_animes:
        mal_id = str(anime['mal_id'])
        if mal_id not in existing_ids:
            missing.append({
                "id": mal_id,
                "title": anime['title'],
                "score": anime.get('score')
            })

    drift_score = len(missing) / limit
    print(f"📊 Drift Score: {drift_score:.2f} ({len(missing)} missing items)")

    result = {
        "status": "success",
        "drift_score": drift_score,
        "missing_items": missing,
        "checked_at": datetime.now().isoformat(),
        "needs_refresh": drift_score > 0.2 # Seuil d'alerte à 20%
    }
    
    # Sauvegarde du rapport
    report_path = os.path.join(BASE_DIR, 'data', 'mlops', 'drift_report_latest.json')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        
    return result

if __name__ == "__main__":
    run_drift_detection()
