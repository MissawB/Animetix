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
INPUT_FILE = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_animes.json')
OUTPUT_FILE = os.path.join(BASE_DIR, 'data', 'processed', 'anime_themes.json')

ANIMETHEMES_API_URL = "https://api.animethemes.moe/anime"

def fetch_themes_for_anime(mal_id: int) -> dict | None:
    """Récupère les thèmes depuis AnimeThemes.moe en utilisant le MAL ID.
    
    Args:
        mal_id: L'identifiant MyAnimeList.
        
    Returns:
        Un dictionnaire contenant les thèmes ou None si aucun n'est trouvé.
    """
    params = {
        "filter[has]": "resources",
        "filter[resource][site]": "MyAnimeList",
        "filter[resource][external_id]": mal_id,
        "include": "animethemes.animethemeentries.videos,animethemes.song.artists"
    }
    try:
        response = requests.get(ANIMETHEMES_API_URL, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json().get('anime', [])
            if data:
                return data[0]
        return None
    except Exception as e:
        print(f"❌ Error fetching themes for MAL ID {mal_id}: {e}")
        return None

def run_fetching(limit: int = 200) -> str:
    """Lance la récupération des thèmes pour une liste d'animés.
    
    Args:
        limit: Nombre maximum d'animés à traiter dans cette passe.
        
    Returns:
        Un message de statut.
    """
    if not os.path.exists(INPUT_FILE):
        return f"❌ Input file not found: {INPUT_FILE}"

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        animes = json.load(f)

    themes_data = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                themes_data = json.load(f)
        except Exception as e:
            print(f"⚠️ Erreur lors du chargement de {OUTPUT_FILE}: {e}")
            pass

    print(f"🚀 Fetching Anime Themes from AnimeThemes.moe (Limit: {limit})...")
    
    count = 0
    processed = 0
    # On trie par popularité pour avoir les plus connus en priorité si possible
    # (Ils sont déjà triés par popularité dans clean_root_animes.json normalement)
    
    for anime in animes:
        if processed >= limit: break
        
        mal_id = anime.get('idMal')
        anime_id = str(anime.get('id'))
        
        if not mal_id or anime_id in themes_data:
            if anime_id in themes_data:
                processed += 1
            continue
            
        print(f"   - [{processed+1}/{limit}] Fetching for: {anime.get('title')}")
        theme_info = fetch_themes_for_anime(mal_id)
        
        if theme_info:
            extracted_themes = []
            for theme in theme_info.get('animethemes', []):
                song = theme.get('song', {})
                artists = [a.get('name') for a in song.get('artists', [])]
                
                entries = []
                for entry in theme.get('animethemeentries', []):
                    videos = []
                    for video in entry.get('videos', []):
                        videos.append({
                            'link': video.get('link'),
                            'resolution': video.get('resolution'),
                            'nc': video.get('nc', False),
                            'subbed': video.get('subbed', False)
                        })
                    entries.append({
                        'version': entry.get('version'),
                        'episodes': entry.get('episodes'),
                        'videos': videos
                    })
                
                extracted_themes.append({
                    'type': theme.get('type'), # OP or ED
                    'sequence': theme.get('sequence'),
                    'song_title': song.get('title'),
                    'artists': artists,
                    'entries': entries
                })
            
            themes_data[anime_id] = {
                'title': anime.get('title'),
                'mal_id': mal_id,
                'themes': extracted_themes
            }
            count += 1
        
        processed += 1
        time.sleep(1.2) # Rate limit friendly
        
        if count > 0 and count % 10 == 0:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(themes_data, f, indent=2, ensure_ascii=False)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(themes_data, f, indent=2, ensure_ascii=False)
    
    status = f"✅ Finished! Added themes for {count} animes. Total in DB: {len(themes_data)}"
    print(status)
    return status

if __name__ == "__main__":
    run_fetching()
