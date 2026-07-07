from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from pipeline.vector_client import vector_manager


class Command(BaseCommand):
    help = (
        "Checks Django database tables, migration status, and vector collection counts."
    )

    def handle(self, *args, **options):
        self.stdout.write("[INFO] Running Database Status Check...\n")

        # 1. Check Django database tables
        self.stdout.write("--- 1. Django Database Tables ---")
        try:
            tables = connection.introspection.table_names()
            self.stdout.write(f"Tables found: {len(tables)}")
            for t in sorted(tables)[:10]:  # Show first 10
                self.stdout.write(f" - {t}")
            if len(tables) > 10:
                self.stdout.write(f" ... and {len(tables) - 10} more.")

            if "animetix_profile" in tables:
                self.stdout.write(
                    self.style.SUCCESS("[SUCCESS] Table animetix_profile EXISTS.")
                )
            else:
                self.stdout.write(
                    self.style.WARNING("[WARNING] Table animetix_profile NOT found.")
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[ERROR] Error checking tables: {e}"))

        # 2. Check Migrations
        self.stdout.write("\n--- 2. Django Migrations ---")
        try:
            executor = MigrationExecutor(connection)
            applied = executor.loader.applied_migrations
            self.stdout.write(f"Applied migrations count: {len(applied)}")
            animetix_migrations = sorted(
                [m[1] for m in applied if m[0] == "animetix"], reverse=True
            )
            self.stdout.write("Latest 'animetix' migrations applied:")
            for m in animetix_migrations[:5]:
                self.stdout.write(f" - {m}")
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"[ERROR] Error checking migrations: {e}")
            )

        # 3. Check Vector Collection Counts
        self.stdout.write("\n--- 3. Vector Collections (Qdrant/PGVector) ---")
        collections = [
            "anime_thematic",
            "anime_visual_vibe",
            "manga_thematic",
            "manga_visual_vibe",
            "movie_thematic",
            "movie_plot",
            "movie_vibe",
            "character_vibe",
            "character_visual_vibe",
            "game_thematic",
            "game_plot",
            "game_vibe",
            "actor_thematic",
            "actor_vibe",
        ]

        for coll_name in collections:
            try:
                coll = vector_manager.get_collection(coll_name)
                count = coll.count()
                self.stdout.write(f"Collection '{coll_name}': {count} items")
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"Collection '{coll_name}': Could not query count ({e})"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS("\n[SUCCESS] Database status check completed.")
        )
