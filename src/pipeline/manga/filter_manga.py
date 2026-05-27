import re
import json
import os
import sys
import logging

logger = logging.getLogger("animetix.pipeline." + __name__)

# Forcer l'encodage UTF-8 pour éviter les erreurs sur Windows avec les emojis
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAW_FILE = os.path.join(BASE_DIR, 'data', 'raw', 'raw_manga_db.json')
OUTPUT_FILE = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_mangas.json')

def clean_description(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    patterns_to_remove = [
        r'\(Source:.*?\)',
        r'\[Written by.*?\]',
        r'Notes?:.*',
        r'Official website:.*',
        r'Originally aired.*',
        r'Adapted from.*',
    ]
    for pattern in patterns_to_remove:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def run_refinement():
    if not os.path.exists(RAW_FILE):
        logger.error(f"❌ Error: {RAW_FILE} not found.")
        return

    logger.info("Loading the raw database...")
    with open(RAW_FILE, 'r', encoding='utf-8') as f:
        all_mangas = json.load(f)

    mangas_map = {
        m['id']: m
        for m in all_mangas
        if m.get('description')
    }

    logger.info(f"{len(mangas_map)} mangas with description loaded.")

    non_root_ids = set()
    RELATIONS_TO_EXCLUDE = ['PREQUEL', 'REMAKE', 'ALTERNATIVE_SETTING', 'ALTERNATIVE_VERSION']

    for m_id, m in mangas_map.items():
        if m['format'] not in ['MANGA', 'ONE_SHOT']:
            non_root_ids.add(m_id)
            continue 

        for edge in m['relations']['edges']:
            if edge['relationType'] in RELATIONS_TO_EXCLUDE:
                non_root_ids.add(m_id)
                break

    logger.info(f"{len(non_root_ids)} mangas identified as non-roots.")

    clean_root_mangas = []
    for m_id, m in mangas_map.items():
        if m_id not in non_root_ids:
            TAG_RELEVANCE_THRESHOLD = 70
            clean_tags = []
            if 'tags' in m and m['tags']:
                for tag in m['tags']:
                    if tag.get('rank') and tag['rank'] >= TAG_RELEVANCE_THRESHOLD:
                        clean_tags.append(tag['name'])

            clean_desc = clean_description(m.get('description'))

            clean_data = {
                'id': m['id'],
                'idMal': m.get('idMal'),
                'title': m['title']['romaji'],
                'title_english': m['title']['english'],
                'title_native': m['title']['native'],
                'description': clean_desc,
                'genres': m['genres'],
                'tags': clean_tags,
                'popularity': m['popularity'],
                'year': m['startDate']['year'] if m['startDate'] else None,
                'image': m['coverImage']['large'] if m['coverImage'] else None,
                'recommendations': {r['mediaRecommendation']['title']['romaji']: r['rating'] for r in m['recommendations']['nodes'] if r.get('mediaRecommendation')} if m.get('recommendations') else {}
            }
            clean_root_mangas.append(clean_data)

    # Sauvegarde
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(clean_root_mangas, f, indent=2, ensure_ascii=False)

    logger.info(f"✅ Clean database saved: {len(clean_root_mangas)} 'root' mangas.")

if __name__ == "__main__":
    run_refinement()
