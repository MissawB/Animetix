import json
import yaml
import os
import sys

# Forcer l'encodage UTF-8 pour éviter les erreurs sur Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_expert_enrichment():
    """
    Parcourt les fichiers JSON transformés et injecte des faits experts basés sur des mots-clés.
    Déplace la logique de 'Hardcoded Injections' vers le pipeline de données.
    """
    # Détection de la racine du projet
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    FACTS_FILE = os.path.join(BASE_DIR, 'src', 'core', 'domain', 'services', 'prompts', 'expert_facts.yaml')
    ANIME_FILE = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_animes.json')
    MANGA_FILE = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_mangas.json')
    CHAR_FILE = os.path.join(BASE_DIR, 'data', 'processed', 'filtered_characters.json')

    if not os.path.exists(FACTS_FILE):
        print(f"❌ Fichier expert_facts.yaml introuvable à {FACTS_FILE}")
        return

    print(f"📖 Chargement des faits experts depuis {FACTS_FILE}...")
    with open(FACTS_FILE, 'r', encoding='utf-8') as f:
        facts_data = yaml.safe_load(f)
    expert_facts = facts_data.get('expert_facts', [])

    files_to_process = [
        (ANIME_FILE, "Anime"),
        (MANGA_FILE, "Manga"),
        (CHAR_FILE, "Character")
    ]

    for file_path, label in files_to_process:
        if not os.path.exists(file_path):
            print(f"⚠️ Fichier non trouvé : {file_path}")
            continue

        print(f"🔄 Enrichissement des {label}s dans {os.path.basename(file_path)}...")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        enriched_items_count = 0
        total_facts_added = 0

        for item in data:
            # Récupération du titre/nom et de l'origine
            title = item.get('title', '')
            name = item.get('name', '')
            origin = item.get('origin', '') # Principalement pour les personnages
            
            search_text = f"{title} {name} {origin}".lower()
            
            item_was_enriched = False
            for fact_entry in expert_facts:
                primary_keywords = fact_entry.get('primary_keywords', [])
                fact = fact_entry.get('fact', "")

                # Correspondance si un mot-clé primaire est présent
                match = any(kw.lower() in search_text for kw in primary_keywords)
                
                if match:
                    # Idempotence : on vérifie si le début du fait est déjà présent
                    fact_prefix = fact[:30]
                    
                    # Choix du champ de description (description pour media, clean_description pour personnages)
                    desc_key = 'description'
                    if 'clean_description' in item:
                        desc_key = 'clean_description'
                    elif 'description' not in item and 'biography' in item:
                        desc_key = 'biography'
                    
                    # Prepend au champ de description principal
                    if desc_key in item:
                        if fact_prefix not in str(item[desc_key]):
                            item[desc_key] = f"{fact}\n\n{item[desc_key]}"
                            item_was_enriched = True
                            total_facts_added += 1
                    
                    # Gestion de synopsis_fr (creation + prepend)
                    if 'synopsis_fr' not in item:
                        # Initialisation avec la description si inexistante
                        item['synopsis_fr'] = item.get(desc_key, "")
                    
                    if fact_prefix not in str(item['synopsis_fr']):
                        item['synopsis_fr'] = f"{fact}\n\n{item['synopsis_fr']}"
                        item_was_enriched = True

            if item_was_enriched:
                enriched_items_count += 1

        # Sauvegarde du fichier mis à jour
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Enrichissement terminé pour {label} : {enriched_items_count} items mis à jour ({total_facts_added} faits injectés).")

if __name__ == "__main__":
    run_expert_enrichment()
