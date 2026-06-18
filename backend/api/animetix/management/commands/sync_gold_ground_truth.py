from django.core.management.base import BaseCommand

from scripts.sync_gold_ground_truth import run_synchronization


class Command(BaseCommand):
    help = "Synchronise automatiquement les Vérités Terrains du Gold Set avec les données du graphe Neo4j."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Exécute le pipeline en mode audit sans enregistrer les modifications.",
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("🚀 Starting Gold Set Ground Truth Synchronization...")
        )

        dry_run = options.get("dry_run", False)
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️ Running in DRY-RUN mode. No changes will be saved."
                )
            )

        res = run_synchronization(dry_run=dry_run)

        if res.get("status") == "error":
            self.stdout.write(
                self.style.ERROR(f"❌ Synchronization failed: {res.get('reason')}")
            )
            return

        updated_count = res.get("updated_count", 0)
        self.stdout.write(
            self.style.SUCCESS(
                f"🏁 Synchronization finished. Updated {updated_count} entries."
            )
        )

        for detail in res.get("details", []):
            self.stdout.write(f"  📝 Query: {detail['query']}")
            self.stdout.write(
                self.style.WARNING(f"    - Drift reason: {detail['reasoning']}")
            )
