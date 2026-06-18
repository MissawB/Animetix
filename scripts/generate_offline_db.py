import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
OUTPUT_DIR = os.path.join(
    BASE_DIR, "src", "backend", "animetix", "static", "animetix", "data"
)
os.makedirs(OUTPUT_DIR, exist_ok=True)

DB_PATH = os.path.join(OUTPUT_DIR, "offline_catalog.db")


def generate_sqlite_catalog(limit=2000):
    """Génère une base SQLite optimisée pour le mode offline dans le navigateur."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Création des tables
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

    # Indexation pour la performance
    cursor.execute("CREATE INDEX idx_media_type ON media(type)")
    cursor.execute("CREATE INDEX idx_tags_name ON tags(name)")

    files = {
        "Anime": "clean_root_animes.json",
        "Manga": "clean_root_mangas.json",
        "Character": "refined_characters.json",
    }

    for m_type, filename in files.items():
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            continue

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

            # Gestion de la popularité (int ou dict)
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
                        item.get("description")[:500]
                        if item.get("description")
                        else "",
                    ),
                )

                # Tags et Genres
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

            print(f"✅ Imported {limit} {m_type} entries into SQLite.")

    conn.commit()
    conn.close()
    print(f"✨ SQLite Offline DB generated at: {DB_PATH}")


if __name__ == "__main__":
    generate_sqlite_catalog()
