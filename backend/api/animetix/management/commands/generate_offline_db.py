import json
import os
import sqlite3

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generates an optimized offline SQLite database of the catalog for browser usage."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=2000,
            help="Limit the number of imported entries per media type.",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        self.stdout.write(f"[INFO] Generating SQLite offline DB (limit: {limit})...")

        # Resolve paths dynamically relative to project root
        project_root = settings.BASE_DIR.parent.parent
        data_dir = os.path.join(project_root, "data", "processed")
        app_dir = os.path.join(settings.BASE_DIR, "animetix")
        output_dir = os.path.join(app_dir, "static", "animetix", "data")

        os.makedirs(output_dir, exist_ok=True)
        db_path = os.path.join(output_dir, "offline_catalog.db")

        if os.path.exists(db_path):
            os.remove(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create Tables
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS media (
            id TEXT PRIMARY KEY,
            type TEXT,
            title TEXT,
            title_en TEXT,
            title_jp TEXT,
            image TEXT,
            popularity INTEGER,
            description TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            media_id TEXT,
            name TEXT,
            type TEXT, -- 'genre' or 'tag'
            FOREIGN KEY(media_id) REFERENCES media(id)
        )
        """)

        # Indexing for performance
        cursor.execute("CREATE INDEX idx_media_type ON media(type)")
        cursor.execute("CREATE INDEX idx_tags_name ON tags(name)")

        files = {
            "Anime": "clean_root_animes.json",
            "Manga": "clean_root_mangas.json",
            "Character": "refined_characters.json",
        }

        for m_type, filename in files.items():
            path = os.path.join(data_dir, filename)
            if not os.path.exists(path):
                self.stdout.write(
                    self.style.WARNING(
                        f"[WARNING] File {filename} not found in {data_dir}. Skipping."
                    )
                )
                continue

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

                # Sort by popularity
                def get_pop(x):
                    p = x.get("popularity", 0)
                    if isinstance(p, dict):
                        return p.get("favourites", 0)
                    return p or 0

                sorted_data = sorted(data, key=get_pop, reverse=True)

                for item in sorted_data[:limit]:
                    m_id = f"{m_type}_{item.get('id')}"
                    pop = get_pop(item)
                    cursor.execute(
                        "INSERT OR REPLACE INTO media (id, type, title, title_en, title_jp, image, popularity, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            m_id,
                            m_type,
                            item.get("title") or item.get("name"),
                            item.get("title_english"),
                            item.get("title_native"),
                            item.get("image"),
                            pop,
                            (
                                item.get("description")[:500]
                                if item.get("description")
                                else ""
                            ),
                        ),
                    )

                    # Genres & Tags
                    genres = item.get("genres", [])
                    tags = item.get("micro_tags", []) or item.get("tags", [])

                    for g in genres:
                        cursor.execute(
                            "INSERT INTO tags (media_id, name, type) VALUES (?, ?, ?)",
                            (m_id, g, "genre"),
                        )
                    for t in tags:
                        cursor.execute(
                            "INSERT INTO tags (media_id, name, type) VALUES (?, ?, ?)",
                            (m_id, t, "tag"),
                        )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"[SUCCESS] Imported {min(len(sorted_data), limit)} {m_type} entries into SQLite."
                    )
                )

        conn.commit()
        conn.close()
        self.stdout.write(
            self.style.SUCCESS(f"[SUCCESS] SQLite Offline DB generated at: {db_path}")
        )
