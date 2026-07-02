import os
import sqlite3
import sys

db_path = sys.argv[1] if len(sys.argv) > 1 else "backend/api/db.sqlite3"
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT name FROM django_migrations WHERE app='animetix' ORDER BY id DESC;"
        )
        migrations = [row[0] for row in cursor.fetchall()]
        print(f"Migrations applied for 'animetix' in {db_path} (reversed):")
        for m in migrations:
            print(f" - {m}")
    except Exception as e:
        print(f"Error reading {db_path}: {e}")
    conn.close()
