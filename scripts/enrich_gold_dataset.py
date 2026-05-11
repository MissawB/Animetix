import json
import os
import time
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Configuration Gemini (Modèle optimisé pour gros volume selon quotas utilisateur)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-3.1-flash-lite-preview"

# Chemins
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANIME_FILE = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_animes.json')
MANGA_FILE = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_mangas.json')
GOLD_FILE = os.path.join(BASE_DIR, 'data', 'mlops', 'gold_dataset.json')

def load_data(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_queries(title, description, genres, tags):
    prompt = f"""Génère 10 requêtes de recherche utilisateur UNIQUES et CRÉATIVES pour l'oeuvre suivante :
    Titre : {title}
    Synopsis : {description[:500]}...
    Genres : {', '.join(genres)}
    Tags : {', '.join(tags[:20])}

    Consignes impératives :
    - Langue : FRANÇAIS uniquement.
    - Diversité : 2 précises, 2 thématiques, 2 basées sur les personnages, 2 "mémoire floue", 2 questions/anecdotes.
    - Réalisme : Simule comment un vrai fan ou un néophyte chercherait sur Google/Animetix.
    - Format : Réponds UNIQUEMENT avec un tableau JSON de strings.

    Exemple de sortie : ["requete 1", "...", "requete 10"]
    """
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
    except Exception as e:
        print(f"❌ Error generating for {title}: {e}")
        return []

def enrich():
    print(f"📂 Loading data (Targeting {MODEL_NAME})...")
    animes = load_data(ANIME_FILE)
    mangas = load_data(MANGA_FILE)
    
    # Sélectionner un échantillon large (top 50 de chaque = 100 requests = 1000 queries)
    # On reste sous les 500 RPD de la table utilisateur
    selected_animes = sorted([a for a in animes if a.get('description')], key=lambda x: x.get('popularity', 0), reverse=True)[:50]
    selected_mangas = sorted([m for m in mangas if m.get('description')], key=lambda x: x.get('popularity', 0), reverse=True)[:50]
    
    new_entries = []
    
    all_targets = selected_animes + selected_mangas
    for i, item in enumerate(all_targets):
        title = item.get('title_english') or item.get('title')
        print(f"[{i+1}/{len(all_targets)}] 🧠 Generating 10 queries for: {title}")
        
        queries = generate_queries(
            title, 
            item.get('description', ''), 
            item.get('genres', []), 
            item.get('tags', [])
        )
        
        for q in queries:
            new_entries.append({
                "query": q,
                "expected_id": str(item['id']),
                "expected_title": title
            })
        
        # RPM Limit: 15 -> 4.5s de pause pour être safe
        time.sleep(4.5)

    # Fusion avec l'existant
    existing_data = load_data(GOLD_FILE)
    existing_queries = {e['query'].lower() for e in existing_data}
    unique_new_entries = [e for e in new_entries if e['query'].lower() not in existing_queries]
    
    combined_data = existing_data + unique_new_entries
    
    os.makedirs(os.path.dirname(GOLD_FILE), exist_ok=True)
    with open(GOLD_FILE, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Gold Dataset enrichi massivement ! Total : {len(combined_data)} entrées.")

if __name__ == "__main__":
    enrich()
