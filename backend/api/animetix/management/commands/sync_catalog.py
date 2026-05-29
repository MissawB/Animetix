import os
import json
from django.core.management.base import BaseCommand
from animetix.models import MediaItem

class Command(BaseCommand):
    help = 'Syncs processed JSON files to the Django relational catalog.'

    def handle(self, *args, **options):
        # Correctly find project root from backend/animetix/management/commands/sync_catalog.py
        # 1: commands, 2: management, 3: animetix, 4: backend, 5: project_root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../../../"))
        data_processed_dir = os.path.join(project_root, 'data', 'processed')
        
        sync_configs = [
            {'file': 'clean_root_animes.json', 'type': 'Anime', 'id_fields': ['idMal', 'mal_id', 'id']},
            {'file': 'clean_root_mangas.json', 'type': 'Manga', 'id_fields': ['idMal', 'mal_id', 'id']},
            {'file': 'filtered_characters.json', 'type': 'Character', 'id_fields': ['id']},
            {'file': 'clean_root_movies.json', 'type': 'Movie', 'id_fields': ['id']},
            {'file': 'clean_root_games.json', 'type': 'Game', 'id_fields': ['id']},
            {'file': 'clean_root_actors.json', 'type': 'Actor', 'id_fields': ['id']},
        ]

        total_synced = 0
        for config in sync_configs:
            path = os.path.join(data_processed_dir, config['file'])
            if not os.path.exists(path):
                self.stdout.write(self.style.WARNING(f"File not found: {path}"))
                continue

            self.stdout.write(f"Syncing {config['type']} from {config['file']}...")
            with open(path, 'r', encoding='utf-8') as f:
                items = json.load(f)

            for item in items:
                # Resolve external ID from multiple possible fields
                ext_id = None
                for field in config['id_fields']:
                    if item.get(field):
                        ext_id = str(item.get(field))
                        break
                
                if not ext_id: continue

                # Mapping common fields
                title = item.get('title') or item.get('name')
                title_en = item.get('title_english') or item.get('title_en')
                title_nat = item.get('title_native') or item.get('title_jp')
                desc = item.get('description') or item.get('synopsis') or item.get('biography') or ""
                img = item.get('image') or item.get('image_url')
                year = item.get('year') or item.get('release_year')
                
                # Robust year parsing
                if isinstance(year, str):
                    if year.isdigit(): year = int(year)
                    else:
                        # Handle cases like "2021-2022" or "2021 (Spring)"
                        import re
                        match = re.search(r'\d{4}', year)
                        year = int(match.group()) if match else None
                elif not isinstance(year, (int, float)):
                    year = None
                
                rating = item.get('rating') or item.get('score')
                if isinstance(rating, str):
                    try: rating = float(rating)
                    except (ValueError, TypeError): rating = None

                # Remove mapped fields from metadata to avoid redundancy
                metadata = item.copy()
                fields_to_pop = config['id_fields'] + ['title', 'name', 'title_english', 'title_en', 'title_native', 'title_jp', 'description', 'synopsis', 'biography', 'image', 'image_url', 'year', 'release_year', 'rating', 'score']
                for f in fields_to_pop:
                    metadata.pop(f, None)

                MediaItem.objects.update_or_create(
                    external_id=ext_id,
                    media_type=config['type'],
                    defaults={
                        'title': title or "Unknown",
                        'title_english': title_en,
                        'title_native': title_nat,
                        'description': desc[:5000] if desc else "",
                        'image_url': img,
                        'release_year': int(year) if year else None,
                        'rating': float(rating) if rating else None,
                        'metadata': metadata
                    }
                )
                total_synced += 1
            
            self.stdout.write(self.style.SUCCESS(f"Finished {config['type']}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully synced {total_synced} items to catalog."))
