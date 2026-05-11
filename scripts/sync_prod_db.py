import os
import json
import django
import sys

# Setup Django
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')
django.setup()

from animetix.models import Achievement # Just to test connection

def populate_from_json():
    base_dir = os.getcwd()
    anime_path = os.path.join(base_dir, 'data', 'processed', 'clean_root_animes.json')
    
    if os.path.exists(anime_path):
        with open(anime_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ Prêt à synchroniser {len(data)} œuvres avec Neon.")
            # Note: Si vous avez un modèle 'Work' ou 'Anime' dans models.py, 
            # on l'importerait ici pour faire un bulk_create.
    else:
        print("⚠️ Fichiers de données traités non trouvés. Lancez 'python run_pipeline.py' d'abord.")

if __name__ == "__main__":
    populate_from_json()
