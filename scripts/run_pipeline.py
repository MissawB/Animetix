import os
import subprocess
import sys
import time

def run_script(script_path):
    script_name = os.path.basename(script_path)
    print(f"\n{'='*60}")
    print(f"🚀 EXÉCUTION : {script_name}")
    print(f"{'='*60}")
    
    # On force l'encodage UTF-8 pour les scripts enfants sur Windows
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    
    # On s'assure d'utiliser l'exécutable python actuel
    result = subprocess.run([sys.executable, script_path], env=env)
    
    if result.returncode != 0:
        print(f"❌ ERREUR dans {script_name}. Arrêt de la pipeline.")
        sys.exit(1)

def main():
    start_time = time.time()
    
    # Ordre de priorité des catégories
    categories = ['characters', 'anime', 'manga', 'movies', 'games', 'actors']
    
    for category in categories:
        print(f"\n--- 📂 PHASE : {category.upper()} ---")
        cat_dir = os.path.join("pipeline", category)
        
        if not os.path.exists(cat_dir):
            continue

        # Liste ordonnée des étapes (essaye avec et sans préfixe)
        steps_patterns = []
        if category == 'characters':
            steps_patterns.append(["1_ingest_vg_characters.py", "ingest_vg_characters.py"])
        
        steps_patterns.extend([
            [f"1_ingest_{category}.py", f"ingest_{category}.py"],
            [f"2_refine_{category}.py", f"refine_{category}.py"], # Ajout de refine si présent
            [f"3_filter_{category}.py", f"filter_{category}.py"],
            [f"5_vectorize_{category}.py", f"vectorize_{category}.py"]
        ])

        # Cas spécial : Vectorisation VG (Hors-jeu)
        if category == 'characters':
            steps_patterns.append(["5_vectorize_vg_characters.py", "vectorize_vg_characters.py"])

        for variants in steps_patterns:
            for step in variants:
                script_path = os.path.join(cat_dir, step)
                if os.path.exists(script_path):
                    run_script(script_path)
                    break # On passe à l'étape suivante dès qu'une variante est trouvée

    # Étape finale : Enrichissement Jikan et Cross-Media
    print("\n--- 🌐 PHASE FINALE : ENRICHISSEMENT & MAPPING ---")
    final_steps = [
        "pipeline/jikan_enrichment.py",
        "pipeline/movies/6_cross_media_mapping.py",
        "pipeline/actors/6_cross_media_mapping.py"
    ]
    for step in final_steps:
        if os.path.exists(step):
            run_script(step)

    total_time = (time.time() - start_time) / 60
    print(f"\n{'*'*60}")
    print(f"✨ PIPELINE ANIMETIX TERMINÉE EN {total_time:.2f} MINUTES")
    print(f"{'*'*60}")

if __name__ == "__main__":
    main()
