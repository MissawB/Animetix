import json
import os
import random

# Chemins
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ANIME_DB = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_animes.json')
MANGA_DB = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_mangas.json')
CHAR_DB = os.path.join(BASE_DIR, 'data', 'processed', 'refined_characters.json')
OUTPUT_DATASET = os.path.join(BASE_DIR, 'data', 'mlops', 'datasets', 'animetix_expert_ft.jsonl')

def clean_text(text):
    if not text: return ""
    # On limite la longueur pour éviter des séquences trop longues qui saturent la VRAM
    return text[:1000].replace('\n', ' ').strip()

def run_generate_instruction_dataset():
    dataset = []

    # 1. TRAITEMENT ANIME (Massif)
    if os.path.exists(ANIME_DB):
        with open(ANIME_DB, 'r', encoding='utf-8') as f:
            animes = json.load(f)
            print(f"📺 Processing ALL {len(animes)} animes...")
            for item in animes:
                title = item.get('title', 'Unknown')
                genres = ", ".join(item.get('genres', []))
                studios = ", ".join(item.get('studios', []))
                tags = ", ".join(item.get('tags', []))
                desc = clean_text(item.get('description', ''))
                
                # Instruction 1 : Résumé général
                dataset.append({
                    "instruction": f"Présente l'anime '{title}' de manière détaillée.",
                    "input": "",
                    "output": f"'{title}' est une œuvre majeure du genre {genres}. Produit par le studio {studios}, cet anime explore les thématiques de {tags}. Synopsis : {desc}"
                })
                # Instruction 2 : Focus Technique
                if studios:
                    dataset.append({
                        "instruction": f"Quel studio a produit '{title}' et de quoi ça parle ?",
                        "input": "",
                        "output": f"L'anime '{title}' a été produit par {studios}. C'est une histoire qui traite de {genres}. Résumé : {desc}"
                    })

    # 2. TRAITEMENT MANGA (Massif)
    if os.path.exists(MANGA_DB):
        with open(MANGA_DB, 'r', encoding='utf-8') as f:
            mangas = json.load(f)
            print(f"📖 Processing ALL {len(mangas)} mangas...")
            for item in mangas:
                title = item.get('title', 'Unknown')
                genres = ", ".join(item.get('genres', []))
                tags = ", ".join(item.get('tags', []))
                desc = clean_text(item.get('description', ''))
                
                # Instruction 1 : Caractéristiques
                dataset.append({
                    "instruction": f"Quelles sont les thématiques principales du manga '{title}' ?",
                    "input": "",
                    "output": f"Le manga '{title}' se distingue par ses thèmes : {tags}. Il s'inscrit dans les genres {genres}. Voici son histoire : {desc}"
                })

    # 3. TRAITEMENT PERSONNAGES (Multi-Instructions par personnage)
    if os.path.exists(CHAR_DB):
        with open(CHAR_DB, 'r', encoding='utf-8') as f:
            chars = json.load(f)
            # On ne garde que les personnages un minimum "importants" pour la qualité (ex: > 50 favorites)
            top_chars = [c for c in chars if c.get('popularity', {}).get('favourites', 0) > 50]
            print(f"🎭 Processing {len(top_chars)} characters (favourites > 50) with triple augmentation...")
            
            for c in top_chars:
                name = c.get('name', 'Anonyme')
                origin = c.get('origin', 'Inconnu')
                
                # Récupération intelligente des traits/pouvoirs depuis les métadonnées de refined
                ents = c.get('entities', {})
                orgs = ", ".join(ents.get('organizations', []))
                
                # Bio nettoyée
                bio = clean_text(c.get('biography', ''))
                if not bio: continue

                # Instruction 1 : Analyse complète
                dataset.append({
                    "instruction": f"Analyse le personnage de {name} dans {origin}.",
                    "input": "",
                    "output": f"{name} est un personnage clé de l'œuvre '{origin}'. Son profil est marqué par ses affiliations à : {orgs}. Biographie : {bio}"
                })

                # Instruction 2 : Identification
                dataset.append({
                    "instruction": f"Qui est {name} ?",
                    "input": f"Contexte : {origin}",
                    "output": f"{name} est un personnage emblématique de {origin}. Bio : {bio}"
                })

    # Mélange du dataset pour un meilleur apprentissage (Shuffle)
    random.shuffle(dataset)

    # Sauvegarde finale en JSONL
    os.makedirs(os.path.dirname(OUTPUT_DATASET), exist_ok=True)
    with open(OUTPUT_DATASET, 'w', encoding='utf-8') as f:
        for entry in dataset:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    print(f"🚀 MASSIVE DATASET READY: {len(dataset)} instructions generated.")
    print(f"📍 Location: {OUTPUT_DATASET}")

if __name__ == "__main__":
    run_generate_instruction_dataset()
