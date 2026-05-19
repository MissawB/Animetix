import requests
import json
import time
import os
import sys

# Force UTF-8 for Windows output
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_FILE = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_mangas.json')
OUTPUT_FILE = os.path.join(BASE_DIR, 'data', 'processed', 'manga_covers.json')

MANGADEX_API_URL = "https://api.mangadex.org"
MALSYNC_API_URL = "https://api.malsync.moe/mal/manga"

def get_mangadex_id(mal_id: int) -> str | None:
    """Récupère l'ID MangaDex à partir de l'ID MAL via MAL-Sync.
    
    Args:
        mal_id: L'identifiant MyAnimeList.
        
    Returns:
        L'ID MangaDex (UUID) ou None.
    """
    try:
        response = requests.get(f"{MALSYNC_API_URL}/{mal_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Dans MAL-Sync, les sites sont des clés dans un dictionnaire
            sites = data.get('Sites', {})
            mangadex_entries = sites.get('Mangadex', {})
            if mangadex_entries:
                # On prend la première entrée (clé est l'ID MangaDex)
                return list(mangadex_entries.keys())[0]
        return None
    except Exception as e:
        print(f"❌ Error mapping MAL ID {mal_id} to MangaDex: {e}")
        return None

def fetch_covers(mangadex_id: str) -> dict:
    """Récupère les covers japonaise et française pour un ID MangaDex.
    
    Args:
        mangadex_id: L'UUID MangaDex.
        
    Returns:
        Un dictionnaire avec les URLs des covers.
    """
    params = {
        "manga[]": [mangadex_id],
        "locales[]": ["ja", "fr"],
        "limit": 100
    }
    covers = {"ja": [], "fr": []}
    try:
        response = requests.get(f"{MANGADEX_API_URL}/cover", params=params, timeout=10)
        if response.status_code == 200:
            data = response.json().get('data', [])
            for item in data:
                attr = item.get('attributes', {})
                locale = attr.get('locale')
                file_name = attr.get('fileName')
                volume = attr.get('volume')
                
                if locale in covers and file_name:
                    url = f"https://uploads.mangadex.org/covers/{mangadex_id}/{file_name}"
                    covers[locale].append({
                        "url": url,
                        "volume": volume
                    })
        return covers
    except Exception as e:
        print(f"❌ Error fetching covers for MangaDex ID {mangadex_id}: {e}")
        return covers

def run_fetching(limit: int = 100) -> str:
    """Lance la récupération des covers pour une liste de mangas.
    
    Args:
        limit: Nombre maximum de mangas à traiter.
        
    Returns:
        Message de statut.
    """
    if not os.path.exists(INPUT_FILE):
        return f"❌ Input file not found: {INPUT_FILE}"

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        mangas = json.load(f)

    covers_data = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                covers_data = json.load(f)
        except Exception as e:
            print(f"⚠️ Erreur lors du chargement de {OUTPUT_FILE}: {e}")
            pass

    print(f"🚀 Fetching Manga Covers (Limit: {limit})...")
    
    count = 0
    processed = 0
    
    for manga in mangas:
        if processed >= limit: break
        
        mal_id = manga.get('idMal')
        manga_id = str(manga.get('id'))
        
        if not mal_id or manga_id in covers_data:
            if manga_id in covers_data:
                processed += 1
            continue
            
        print(f"   - [{processed+1}/{limit}] Processing: {manga.get('title')}")
        
        md_id = get_mangadex_id(mal_id)
        if md_id:
            covers = fetch_covers(md_id)
            if covers["ja"] or covers["fr"]:
                covers_data[manga_id] = {
                    "title": manga.get('title'),
                    "mangadex_id": md_id,
                    "covers": covers
                }
                count += 1
        
        processed += 1
        time.sleep(1.0) # Respect rate limits
        
        if count > 0 and count % 10 == 0:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(covers_data, f, indent=2, ensure_ascii=False)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(covers_data, f, indent=2, ensure_ascii=False)
    
    status = f"✅ Finished! Added covers for {count} mangas. Total in DB: {len(covers_data)}"
    print(status)
    return status

if __name__ == "__main__":
    run_fetching()
