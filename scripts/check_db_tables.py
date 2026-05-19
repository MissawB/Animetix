import sqlite3
import os

db_path = 'src/backend/db.sqlite3'
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print("Tables found:")
    for t in tables:
        print(f" - {t}")
    if 'animetix_aitokenusage' in tables:
        print("\n✅ Table animetix_aitokenusage EXISTS.")
    else:
        print("\n❌ Table animetix_aitokenusage MISSING.")
    conn.close()
