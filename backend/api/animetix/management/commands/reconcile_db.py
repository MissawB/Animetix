from django.core.management.base import BaseCommand
from pipeline.neo4j_client import neo4j_manager
from pipeline.vector_client import vector_manager

from animetix.models import MediaItem, VectorRecord


class Command(BaseCommand):
    help = "Reconciles database catalog items across Django, pgvector, and Neo4j."

    def handle(self, *args, **options):
        self.stdout.write("[INFO] Starting Database Reconciliation...\n")

        # 1. Get Source of Truth (Django)
        items = MediaItem.objects.all()
        count = items.count()
        self.stdout.write(f"[INFO] Catalog Source: {count} items in Django.")

        if count == 0:
            self.stdout.write(
                self.style.WARNING(
                    "[WARNING] Django catalog is empty. Run 'python manage.py sync_catalog' first."
                )
            )
            return

        # 2. Check external service connectivity once to avoid loop logging floods
        self.stdout.write("[INFO] Checking external service connectivity...")

        neo4j_available = neo4j_manager.driver is not None
        if neo4j_available:
            self.stdout.write("[INFO] Neo4j connection is active.")
        else:
            self.stdout.write(
                self.style.WARNING(
                    "[WARNING] Neo4j is offline (driver is None). Skipping Neo4j checks."
                )
            )

        vector_available = True
        try:
            vector_manager.get_collection("anime_thematic")
            self.stdout.write("[INFO] Vector database connection is active.")
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f"[WARNING] Vector database is offline or connection failed ({e}). Skipping Vector checks."
                )
            )
            vector_available = False

        # 3. Check items
        collections = {
            "Anime": ["anime_thematic", "anime_visual_vibe", "anime_plot"],
            "Manga": ["manga_thematic", "manga_visual_vibe"],
            "Character": ["character_vibe", "character_visual_vibe"],
            "Movie": ["movie_thematic", "movie_plot", "movie_vibe"],
            "Game": ["game_thematic", "game_plot", "game_vibe"],
            "Actor": ["actor_vibe"],
        }

        discrepancies = []

        # Sample check for performance (or full if count < 1000)
        check_items = items[:1000] if count > 1000 else items

        self.stdout.write(
            f"[INFO] Verifying {len(check_items)} sample items across DBs..."
        )

        # Bulk fetch existing vectors in Django DB to avoid N+1 query loops
        existing_vectors = set()
        if vector_available:
            try:
                check_item_ids = [str(item.external_id) for item in check_items]
                existing_vectors = set(
                    VectorRecord.objects.filter(item_id__in=check_item_ids).values_list(
                        "collection_name", "item_id"
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"[ERROR] Failed to bulk fetch VectorRecords: {e}")
                )
                vector_available = False

        for item in check_items:
            issues = []

            # pgvector Check
            if vector_available:
                colls = collections.get(item.media_type, [])
                for coll_name in colls:
                    if (coll_name, str(item.external_id)) not in existing_vectors:
                        issues.append(f"Missing in pgvector:{coll_name}")

            # Neo4j Check
            if neo4j_available:
                try:
                    query = f"MATCH (n:{item.media_type} {{id: $id}}) RETURN n LIMIT 1"
                    res = neo4j_manager.execute_query(query, {"id": item.external_id})
                    if not res:
                        issues.append("Missing in Neo4j")
                except Exception:
                    issues.append("Neo4j Check Failed")

            if issues:
                discrepancies.append({"item": str(item), "issues": issues})

        # 4. Report
        checked = ["Django"]
        skipped = []
        (checked if vector_available else skipped).append("pgvector")
        (checked if neo4j_available else skipped).append("Neo4j")

        if discrepancies:
            self.stdout.write(
                self.style.ERROR(f"[ERROR] FOUND {len(discrepancies)} DISCREPANCIES:")
            )
            for d in discrepancies[:20]:  # Show first 20
                self.stdout.write(f"  - {d['item']}: {', '.join(d['issues'])}")

            if len(discrepancies) > 20:
                self.stdout.write(f"  ... and {len(discrepancies) - 20} more.")
        elif skipped:
            # No discrepancies among the stores we could reach -- but do NOT
            # issue a clean bill of health for a store we never checked. A dead
            # Neo4j URI (the whole point of this guard) must not read as
            # "synchronized across ... Neo4j": the verdict names what was
            # verified and what was skipped, so the skip cannot pass unnoticed.
            were = "was" if len(skipped) == 1 else "were"
            self.stdout.write(
                self.style.WARNING(
                    "[WARNING] No discrepancies among the checked stores "
                    f"({', '.join(checked)}), but {', '.join(skipped)} {were} "
                    "SKIPPED (offline): synchronization there is UNVERIFIED, not "
                    "confirmed."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "[SUCCESS] All sampled items are synchronized across Django, pgvector, and Neo4j."
                )
            )
