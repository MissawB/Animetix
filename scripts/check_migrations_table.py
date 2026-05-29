import sqlite3
import os

db_path = 'backend/api/db.sqlite3'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM django_migrations WHERE app='animetix' ORDER BY id DESC;")
migrations = [row[0] for row in cursor.fetchall()]
print("Migrations applied for 'animetix' (reversed):")
for m in migrations:
    print(f" - {m}")
conn.close()
